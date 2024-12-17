from abc import ABC
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.taskrunner.task import Task
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.trade_model import TradeModel

logger = get_logger(__name__)


class TradeTask(Task["TradeModel"], ABC):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)

        self.trade = model
        self.process_model = model.process_model

    def complete(self):
        self.process_model.trade_manager.request_persistence()

        super().complete()

    def failed(self, message=None, exc=None):
        if message:
            self.append_to_error_message(message)
        elif exc:
            logger.error(exc, exc_info=exc)
            self.append_to_error_message(exc)

        self.trade.error_message = self.error_message
        self.process_model.trade_manager.request_persistence()
        super().failed()
