
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask


class MakerVerifyTakerFeePayment(TradeTask):
    
    def run(self):
        try:
            self.run_intercept_hook()

            # JAVA TODO missing impl.

            self.complete()
        except Exception as e:
            self.failed(exc=e)
