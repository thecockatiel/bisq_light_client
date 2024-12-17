from typing import TYPE_CHECKING
from bisq.core.support.dispute.mediation.mediation_result_state import MediationResultState
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.trade.protocol.bisq_v1.tasks.setup_payout_tx_listener import SetupPayoutTxListener

if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade


class SetupMediatedPayoutTxListener(SetupPayoutTxListener):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        
    def run(self):
        try:
            self.run_intercept_hook()
            
            super().run()
        except Exception as e:
            self.failed(exc=e)
            
    def set_state(self):
        self.trade.mediation_result_state = MediationResultState.PAYOUT_TX_SEEN_IN_NETWORK
        
        if self.trade.payout_tx:
            self.process_model.trade_manager.close_disputed_trade(self.trade.get_id(), TradeDisputeState.MEDIATION_CLOSED)
        
        self.process_model.trade_manager.request_persistence()
