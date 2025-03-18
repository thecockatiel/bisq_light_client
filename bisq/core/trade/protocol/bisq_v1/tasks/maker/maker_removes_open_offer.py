from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none


class MakerRemovesOpenOffer(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            self.process_model.open_offer_manager.close_open_offer(
                check_not_none(
                    self.trade.get_offer(),
                    "offer must not be None at MakerRemovesOpenOffer",
                )
            )

            self.complete()
        except Exception as e:
            self.failed(exc=e)
