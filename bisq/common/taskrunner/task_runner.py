from bisq.common.setup.log_setup import get_logger
from bisq.common.taskrunner.task import Task
from bisq.common.taskrunner.task_model import TaskModel
from queue import Queue
from typing import TYPE_CHECKING, Type, TypeVar, Generic

if TYPE_CHECKING:
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.common.handlers.result_handler import ResultHandler

logger = get_logger(__name__)

T = TypeVar("T", bound=TaskModel)


class TaskRunner(Generic[T]):
    def __init__(
        self,
        shared_model: T,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        self.tasks: Queue[Type[Task[T]]] = Queue()
        self.shared_model = shared_model
        self.result_handler = result_handler
        self.error_message_handler = error_message_handler
        self.failed = False
        self.is_canceled = False
        self.current_task: Type[Task[T]] = None

    def add_tasks(self, *items: Type[Task[T]]) -> None:
        for item in items:
            self.tasks.put(item)

    def run(self) -> None:
        self._next()

    def _next(self) -> None:
        if not self.failed and not self.is_canceled:
            if not self.tasks.empty():
                try:
                    self.current_task = self.tasks.get()
                    logger.info(f"Run task: {self.current_task!r}")
                    self.current_task(self, self.shared_model).run()
                except Exception as e:
                    self.handle_error_message(f"Error at taskRunner: {str(e)}", e)
            else:
                self.result_handler()

    def cancel(self) -> None:
        self.is_canceled = True

    def handle_complete(self) -> None:
        self._next()

    def handle_error_message(
        self, error_message: str, exc: BaseException = None
    ) -> None:
        logger.error(
            f"Task failed: {self.current_task!r} / errorMessage: {error_message}",
            exc_info=exc,
        )
        self.failed = True
        self.error_message_handler(error_message)
