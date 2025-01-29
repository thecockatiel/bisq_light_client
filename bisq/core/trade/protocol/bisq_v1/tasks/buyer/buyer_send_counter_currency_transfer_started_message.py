from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.network.message_state import MessageState
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.messages.counter_currency_transfer_started_message import (
    CounterCurrencyTransferStartedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.send_mailbox_message_task import (
    SendMailboxMessageTask,
)
from utils.data import SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.common.timer import Timer
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade

logger = get_logger(__name__)


class BuyerSendCounterCurrencyTransferStartedMessage(SendMailboxMessageTask):
    """
    We send the seller the BuyerSendCounterCurrencyTransferStartedMessage.
    We wait to receive a ACK message back and resend the message
    in case that does not happen in 10 minutes or if the message was stored in mailbox or failed. We keep repeating that
    with doubling the interval each time and until the MAX_RESEND_ATTEMPTS is reached.
    If never successful we give up and complete. It might be a valid case that the peer was not online for an extended
    time but we can be very sure that our message was stored as mailbox message in the network and one the peer goes
    online he will process it.
    """

    MAX_RESEND_ATTEMPTS = 10

    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)
        self.delay_in_min = 15
        self.resend_counter = 0
        self.message: Optional["CounterCurrencyTransferStartedMessage"] = None
        self.listener: Optional[
            Callable[[SimplePropertyChangeEvent["MessageState"]], None]
        ] = None
        self.timer: Optional["Timer"] = None

    def get_trade_mailbox_message(
        self, trade_id: str
    ) -> "CounterCurrencyTransferStartedMessage":
        if self.message is None:
            payout_address_entry = (
                self.trade.process_model.btc_wallet_service.get_or_create_address_entry(
                    trade_id, AddressEntryContext.TRADE_PAYOUT
                )
            )

            # We do not use a real unique ID here as we want to be able to re-send the exact same message in case the
            # peer does not respond with an ACK msg in a certain time interval. To avoid that we get dangling mailbox
            # messages where only the one which gets processed by the peer would be removed we use the same uid. All
            # other data stays the same when we re-send the message at any time later.
            deterministic_id = (
                trade_id + self.process_model.my_node_address.get_full_address()
            )
            self.message = CounterCurrencyTransferStartedMessage(
                trade_id=trade_id,
                buyer_payout_address=payout_address_entry.get_address_string(),
                sender_node_address=self.process_model.my_node_address,
                buyer_signature=self.process_model.payout_tx_signature,
                counter_currency_tx_id=self.trade.counter_currency_tx_id,
                counter_currency_extra_data=self.trade.counter_currency_extra_data,
                uid=deterministic_id,
            )
        return self.message

    def set_state_sent(self):
        if (
            self.trade.get_trade_state().value
            < TradeState.BUYER_SENT_FIAT_PAYMENT_INITIATED_MSG.value
        ):
            self.trade.set_state_if_valid_transition_to(
                TradeState.BUYER_SENT_FIAT_PAYMENT_INITIATED_MSG
            )

        self.process_model.trade_manager.request_persistence()

    def set_state_arrived(self):
        # the message has arrived but we're ultimately waiting for an AckMessage response
        if not self.trade.is_payout_published:
            self._try_to_send_again_later()

    # We override the default behaviour for onStoredInMailbox and do not call complete
    def on_stored_in_mailbox(self):
        self.set_state_stored_in_mailbox()

    def set_state_stored_in_mailbox(self):
        self.trade.set_state_if_valid_transition_to(
            TradeState.BUYER_STORED_IN_MAILBOX_FIAT_PAYMENT_INITIATED_MSG
        )
        if not self.trade.is_payout_published:
            self._try_to_send_again_later()
        self.process_model.trade_manager.request_persistence()

    # We override the default behaviour for onFault and do not call appendToErrorMessage and failed
    def on_fault(self, error_message: str, message: "TradeMessage"):
        self.set_state_fault()

    def set_state_fault(self):
        self.trade.set_state_if_valid_transition_to(
            TradeState.BUYER_SEND_FAILED_FIAT_PAYMENT_INITIATED_MSG
        )
        if not self.trade.is_payout_published:
            self._try_to_send_again_later()
        self.process_model.trade_manager.request_persistence()

    def run(self):
        try:
            self.run_intercept_hook()
            super().run()
        except Exception as e:
            self.failed(exc=e)
        finally:
            self._cleanup()

    # complete() is called from base class SendMailboxMessageTask=>onArrived()
    # We override the default behaviour for complete and keep this task open until receipt of the AckMessage
    def complete(self):
        self._on_message_state_change(
            self.process_model.payment_started_message_state_property.get()
        )  # check for AckMessage

    def _cleanup(self):
        if self.timer is not None:
            self.timer.stop()
        if self.listener is not None:
            self.process_model.payment_started_message_state_property.remove_listener(
                self.listener
            )
            self.listener = None

    def _try_to_send_again_later(self):
        if (
            self.resend_counter
            >= BuyerSendCounterCurrencyTransferStartedMessage.MAX_RESEND_ATTEMPTS
        ):
            self._cleanup()
            logger.warning(
                "We never received an ACK message when sending the CounterCurrencyTransferStartedMessage to the peer. "
                "We stop now and complete the protocol task."
            )
            self.complete()
            return

        logger.info(
            f"We will send the message again to the peer after a delay of {self.delay_in_min} min."
        )
        if self.timer is not None:
            self.timer.stop()
        self.timer = UserThread.run_after(
            self.run, timedelta(minutes=self.delay_in_min)
        )

        if self.listener is None:
            # We want to register listener only once
            self.listener = lambda e: self._on_message_state_change(e.new_value)
            self.process_model.payment_started_message_state_property.add_listener(
                self.listener
            )
            self._on_message_state_change(
                self.process_model.payment_started_message_state_property.get()
            )

        self.delay_in_min *= 2
        self.resend_counter += 1

    def _on_message_state_change(self, new_value: MessageState):
        # Once we receive an ACK from our msg we know the peer has received the msg and we stop.
        if new_value == MessageState.ACKNOWLEDGED:
            # We treat an ACK like BUYER_SAW_ARRIVED_FIAT_PAYMENT_INITIATED_MSG
            self.trade.set_state_if_valid_transition_to(
                TradeState.BUYER_SAW_ARRIVED_FIAT_PAYMENT_INITIATED_MSG
            )

            self.process_model.trade_manager.request_persistence()
            UserThread.execute(self._cleanup)
            self.complete()  # received AckMessage, complete this task
