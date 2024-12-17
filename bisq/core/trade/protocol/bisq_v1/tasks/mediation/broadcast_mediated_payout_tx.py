
from typing import TYPE_CHECKING
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.trade.protocol.bisq_v1.tasks.broadcast_payout_tx import BroadcastPayoutTx

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

class BroadcastMediatedPayoutTx(BroadcastPayoutTx):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        
    def run(self):
        try:
            self.run_intercept_hook()
            
            super().run()
        except Exception as e:
            self.failed(exc=e)
            
    def set_state(self):
        self.trade.mediation_result_state = MediationResultState.PAYOUT_TX_PUBLISHED
        self.process_model.trade_manager.request_persistence()
