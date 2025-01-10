from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from utils.data import SimplePropertyChangeEvent
from bisq.core.network.message_state import MessageState
from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import DepositTxAndDelayedPayoutTxMessage
from bisq.core.trade.protocol.bisq_v1.tasks.send_mailbox_message_task import SendMailboxMessageTask

if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner 
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.trade.protocol.trade_message import TradeMessage

logger = get_logger(__name__)

class SellerSendsDepositTxAndDelayedPayoutTxMessage(SendMailboxMessageTask):
    MAX_RESEND_ATTEMPTS = 7

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.delay_in_sec = 4
        self.resend_counter = 0
        self.message: "DepositTxAndDelayedPayoutTxMessage" = None
        self.listener: Optional[Callable[[SimplePropertyChangeEvent[MessageState]], None]] = None
        self.timer: Optional[Timer] = None
    
    def get_trade_mailbox_message(self, trade_id: str):
        if self.message is None:
            # We do not use a real unique ID here as we want to be able to re-send the exact same message in case the
            # peer does not respond with an ACK msg in a certain time interval. To avoid that we get dangling mailbox
            # messages where only the one which gets processed by the peer would be removed we use the same uid. All
            # other data stays the same when we re-send the message at any time later.
            deterministic_id = trade_id + self.process_model.my_node_address.get_full_address()
            seller_payment_account_payload = self.process_model.get_payment_account_payload(self.trade)
            assert self.process_model.deposit_tx is not None
            assert self.trade.delayed_payout_tx is not None
            self.message = DepositTxAndDelayedPayoutTxMessage(
                uid=deterministic_id,
                trade_id=self.process_model.offer_id,
                sender_node_address=self.process_model.my_node_address,
                deposit_tx=self.process_model.deposit_tx.bitcoin_serialize(),
                delayed_payout_tx=self.trade.delayed_payout_tx.bitcoin_serialize(),
                seller_payment_account_payload=seller_payment_account_payload,
            )
        return self.message
    
    def set_state_sent(self):
        # we no longer set deprecated state (Trade.State.SELLER_SENT_DEPOSIT_TX_PUBLISHED_MSG);
        # see https://github.com/bisq-network/bisq/pull/5746#issuecomment-939879623
        pass
    
    def set_state_arrived(self):
        # we no longer set deprecated state (Trade.State.SELLER_SAW_ARRIVED_DEPOSIT_TX_PUBLISHED_MSG);
        # see https://github.com/bisq-network/bisq/pull/5746#issuecomment-939879623

        self.cleanup()
        # Complete is called in base class

    # We override the default behaviour for onStoredInMailbox and do not call complete
    def on_stored_in_mailbox(self):
        self.set_state_stored_in_mailbox()
        
    def set_state_stored_in_mailbox(self):
        # we no longer set deprecated state (Trade.State.SELLER_STORED_IN_MAILBOX_DEPOSIT_TX_PUBLISHED_MSG);
        # see https://github.com/bisq-network/bisq/pull/5746#issuecomment-939879623

        # The DepositTxAndDelayedPayoutTxMessage is a mailbox message as earlier we use only the deposit tx which can
        # be also received from the network once published.
        # Now we send the delayed payout tx as well and with that this message is mandatory for continuing the protocol.
        # We do not support mailbox message handling during the take offer process as it is expected that both peers
        # are online.
        # For backward compatibility and extra resilience we still keep DepositTxAndDelayedPayoutTxMessage as a
        # mailbox message but the stored in mailbox case is not expected and the seller would try to send the message again
        # in the hope to reach the buyer directly.
        if not self.trade.is_deposit_confirmed:
            self.try_to_send_again_later()
    
    # We override the default behaviour for onFault and do not call appendToErrorMessage and failed
    def on_fault(self, error_message: str, message: "TradeMessage"):
        self.set_state_fault()
        
    def set_state_fault(self):
        # we no longer set deprecated state (Trade.State.SELLER_SEND_FAILED_DEPOSIT_TX_PUBLISHED_MSG);
        # see https://github.com/bisq-network/bisq/pull/5746#issuecomment-939879623
        if not self.trade.is_deposit_confirmed:
            self.try_to_send_again_later()
    
    def run(self):
        try:
            self.run_intercept_hook()
            
            super().run()
        except Exception as e:
            self.failed(exc=e)
        finally:
            self.cleanup()
            
    def cleanup(self):
        if self.timer:
            self.timer.stop()
        if self.listener:
            self.process_model.payment_started_message_state_property.remove_listener(self.listener)
            
    def try_to_send_again_later(self):
        if self.resend_counter >= SellerSendsDepositTxAndDelayedPayoutTxMessage.MAX_RESEND_ATTEMPTS:
            self.cleanup()
            self.failed("We never received an ACK message when sending the msg to the peer. "
                        "We fail here and do not publish the deposit tx.")
            return
        
        logger.info(f"We send the message again to the peer after a delay of {self.delay_in_sec} sec.")
        if self.timer:
            self.timer.stop()
        self.timer = UserThread.run_after(self.run, timedelta(seconds=self.delay_in_sec))
        
        if self.resend_counter == 0:
            # We want to register listener only once
            self.listener = lambda e: self.on_message_state_changed(e.new_value)
            self.process_model.payment_started_message_state_property.add_listener(self.listener)
            self.on_message_state_changed(self.process_model.deposit_tx_message_state_property.value)
        
        self.delay_in_sec *= 2
        self.resend_counter += 1
    
    def on_message_state_changed(self, new_value: MessageState):
        # Once we receive an ACK from our msg we know the peer has received the msg and we stop.
        if new_value == MessageState.ACKNOWLEDGED:
            # We treat a ACK like SELLER_SAW_ARRIVED_DEPOSIT_TX_PUBLISHED_MSG
            # we no longer set deprecated state (Trade.State.SELLER_SAW_ARRIVED_DEPOSIT_TX_PUBLISHED_MSG);
            # see https://github.com/bisq-network/bisq/pull/5746#issuecomment-939879623
            self.cleanup()
            self.complete()
