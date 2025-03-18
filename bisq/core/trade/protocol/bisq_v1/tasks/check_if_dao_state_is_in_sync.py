from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_argument


class CheckIfDaoStateIsInSync(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            check_argument(
                self.process_model.dao_facade.is_dao_state_ready_and_in_sync,
                "DAO state is not in sync with seed nodes",
            )
            self.complete()
        except Exception as e:
            self.failed(exc=e)
