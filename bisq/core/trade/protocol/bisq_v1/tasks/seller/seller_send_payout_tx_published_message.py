from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.messages.payout_tx_published_message import PayoutTxPublishedMessage
from bisq.core.trade.protocol.bisq_v1.tasks.send_mailbox_message_task import (
    SendMailboxMessageTask,
)

if TYPE_CHECKING:
    from bisq.core.trade.protocol.bisq_v1.messages.trade_mailbox_message import TradeMailboxMessage
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.account.sign.signed_witness import SignedWitness


class SellerSendPayoutTxPublishedMessage(SendMailboxMessageTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)
        self.signed_witness: Optional[SignedWitness] = None

    def get_trade_mailbox_message(self, id: str) -> "TradeMailboxMessage":
        assert self.trade.payout_tx is not None, "trade.payout_tx must not be None"
        payout_tx = self.trade.payout_tx
        
        account_age_witness_service = self.process_model.account_age_witness_service
        if account_age_witness_service.is_sign_witness_trade(self.trade):
            # Broadcast is done in accountAgeWitness domain.
            witness = account_age_witness_service.trader_sign_and_publish_peers_account_age_witness(self.trade)
            if witness:
                self.signed_witness = witness
                
        return PayoutTxPublishedMessage(
            trade_id=id,
            payout_tx=payout_tx.bitcoin_serialize(),
            sender_node_address=self.process_model.my_node_address,
            signed_witness=self.signed_witness
        )
    
    def set_state_sent(self) -> None:
        self.trade.state_property.set(TradeState.SELLER_SENT_PAYOUT_TX_PUBLISHED_MSG)
        self.logger.info(f"Sent PayoutTxPublishedMessage: trade_id={self.trade.get_id()} at peer {self.trade.trading_peer_node_address} SignedWitness {self.signed_witness}")
        self.process_model.trade_manager.request_persistence()

    def set_state_arrived(self) -> None:
        self.trade.state_property.set(TradeState.SELLER_SAW_ARRIVED_PAYOUT_TX_PUBLISHED_MSG)
        self.logger.info(f"PayoutTxPublishedMessage arrived: trade_id={self.trade.get_id()} at peer {self.trade.trading_peer_node_address} SignedWitness {self.signed_witness}")
        self.process_model.trade_manager.request_persistence()

    def set_state_stored_in_mailbox(self) -> None:
        self.trade.state_property.set(TradeState.SELLER_STORED_IN_MAILBOX_PAYOUT_TX_PUBLISHED_MSG)
        self.logger.info(f"PayoutTxPublishedMessage storedInMailbox: trade_id={self.trade.get_id()} at peer {self.trade.trading_peer_node_address} SignedWitness {self.signed_witness}")
        self.process_model.trade_manager.request_persistence()

    def set_state_fault(self) -> None:
        self.trade.state_property.set(TradeState.SELLER_SEND_FAILED_PAYOUT_TX_PUBLISHED_MSG)
        self.logger.error(f"PayoutTxPublishedMessage failed: trade_id={self.trade.get_id()} at peer {self.trade.trading_peer_node_address} SignedWitness {self.signed_witness}")
        self.process_model.trade_manager.request_persistence()

    def run(self) -> None:
        try:
            self.run_intercept_hook()

            if self.trade.payout_tx is None:
                self.logger.error("PayoutTx is null")
                self.failed("PayoutTx is null")
                return

            super().run()
        except Exception as e:
            self.failed(exc=e)
