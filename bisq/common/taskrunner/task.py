from typing import TYPE_CHECKING, TypeVar, Generic, Union
from abc import ABC, abstractmethod
from bisq.common.taskrunner.intercept_task_exception import InterceptTaskException

if TYPE_CHECKING:
    from bisq.common.taskrunner.task_runner import TaskRunner


T = TypeVar("T")


class Task(ABC, Generic[T]):
    task_to_intercept = None

    def __init__(self, task_handler: "TaskRunner", model: T):
        self.task_handler = task_handler
        self.model = model
        self.error_message = f"An error occurred at task: {self.__class__.__name__}"
        self.completed = False

    @abstractmethod
    def run(self) -> None:
        pass

    def run_intercept_hook(self) -> None:
        if self.__class__ == Task.task_to_intercept:
            raise InterceptTaskException(
                f"Task intercepted for testing purpose. Task = {self.__class__.__name__}"
            )

    def append_to_error_message(self, message: Union[str, Exception]) -> None:
        self.error_message += f"\n{message}"

    def complete(self) -> None:
        self.completed = True
        self.task_handler.handle_complete()

    def failed(self, message: str = None, exc: Exception = None) -> None:
        if message:
            self.append_to_error_message(message)
        elif exc:
            self.append_to_error_message(str(exc))

        self.task_handler.handle_error_message(self.error_message, exc)
