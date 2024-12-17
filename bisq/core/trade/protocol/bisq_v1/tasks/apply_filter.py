from typing import TYPE_CHECKING
from bisq.core.trade.bisq_v1.trade_util import TradeUtil
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


class ApplyFilter(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)

    def run(self):
        try:
            self.run_intercept_hook()

            node_address = self.process_model.temp_trading_peer_node_address
            assert node_address is not None, "Node address must not be None"

            payment_account_payload = (
                self.process_model.trade_peer.payment_account_payload
            )
            filter_manager = self.process_model.filter_manager

            TradeUtil.apply_filter(
                self.trade,
                filter_manager,
                node_address,
                payment_account_payload,
                self.complete,
                self.failed,
            )
        except Exception as e:
            self.failed(exc=e)
