
from typing import TYPE_CHECKING, cast
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.trade.protocol.bisq_v1.messages.mediated_payout_tx_signature_message import MediatedPayoutTxSignatureMessage
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

class ProcessMediatedPayoutSignatureMessage(TradeTask):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        
    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            if not isinstance(message, MediatedPayoutTxSignatureMessage):
                raise ValueError(f"Invalid message type. expected type: MediatedPayoutTxSignatureMessage, actual type: {type(message)}")
            Validator.check_trade_id(self.process_model.offer_id, message)
            assert message is not None
            
            assert message.tx_signature is not None, "tx_signature must not be None"
            self.process_model.trade_peer.mediated_payout_tx_signature = message.tx_signature
            
            # update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = self.process_model.temp_trading_peer_node_address
            
            self.trade.mediation_result_state = MediationResultState.RECEIVED_SIG_MSG
            
            self.process_model.trade_manager.request_persistence()
            
            self.complete()
        except Exception as e:
            self.failed(exc=e)
