
from abc import ABC, abstractmethod
from collections.abc import Callable


class ErrorMessageHandler(Callable[[str], None], ABC):
    @abstractmethod
    def handle_error_message(error_message: str):
        pass
    
    def __call__(self, message: str) -> None:
        self.handle_error_message(message)