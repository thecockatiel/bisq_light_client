from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.common.taskrunner.task_runner import TaskRunner

if TYPE_CHECKING:
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.common.handlers.result_handler import ResultHandler
    from bisq.core.trade.model.trade_model import TradeModel


class TradeTaskRunner(TaskRunner["TradeModel"]):

    def __init__(
        self,
        shared_model: "TradeModel",
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        super().__init__(shared_model, result_handler, error_message_handler)
        self.logger = get_ctx_logger(__name__)

    # TODO: double check along with TaskRunner
