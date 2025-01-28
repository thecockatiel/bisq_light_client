from abc import ABC, abstractmethod


class ErrorMessageHandler(ABC):

    @abstractmethod
    def __call__(self, error_message: str) -> None:
        pass
