from abc import ABC, abstractmethod
from collections.abc import Callable

# For reporting a description message and exception
class FaultHandler(Callable[[str, Exception], None], ABC):
    @abstractmethod
    def handle_fault(self, error_message: str, exception: Exception) -> None:
        pass

    def __call__(self, error_message: str, exception: Exception) -> None:
        self.handle_fault(error_message, exception)
