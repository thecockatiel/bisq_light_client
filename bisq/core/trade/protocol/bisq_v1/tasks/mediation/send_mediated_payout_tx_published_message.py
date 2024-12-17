from typing import TYPE_CHECKING
import uuid
from bisq.common.setup.log_setup import get_logger
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_signature_message import MediatedPayoutTxSignatureMessage
from bisq.core.trade.protocol.bisq_v1.tasks.send_mailbox_message_task import SendMailboxMessageTask

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

logger = get_logger(__name__)


class SendMediatedPayoutTxPublishedMessage(SendMailboxMessageTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)

    def get_trade_mailbox_message(self, id: str):
        payout_tx = self.trade.get_payout_tx()
        assert payout_tx is not None, "trade.get_payout_tx() must not be None"
        
        return MediatedPayoutTxSignatureMessage(
            trade_id=id,
            tx_signature=payout_tx.bitcoin_serialize(),
            sender_node_address=self.process_model.my_node_address,
            uid=str(uuid.uuid4())
        )

    def set_state_sent(self):
        self.trade.mediation_result_state = MediationResultState.PAYOUT_TX_PUBLISHED_MSG_SENT
        self.process_model.trade_manager.request_persistence()

    def set_state_arrived(self):
        self.trade.mediation_result_state = MediationResultState.PAYOUT_TX_PUBLISHED_MSG_ARRIVED
        self.process_model.trade_manager.request_persistence()

    def set_state_stored_in_mailbox(self):
        self.trade.mediation_result_state = MediationResultState.PAYOUT_TX_PUBLISHED_MSG_IN_MAILBOX
        self.process_model.trade_manager.request_persistence()

    def set_state_fault(self):
        self.trade.mediation_result_state = MediationResultState.PAYOUT_TX_PUBLISHED_MSG_SEND_FAILED
        self.process_model.trade_manager.request_persistence()

    def run(self):
        try:
            self.run_intercept_hook()

            if self.trade.get_payout_tx() is None:
                msg = "PayoutTx is None"
                logger.error(msg)
                self.failed(msg)
                return
                
            super().run()
        except Exception as e:
            self.failed(exc=e)
