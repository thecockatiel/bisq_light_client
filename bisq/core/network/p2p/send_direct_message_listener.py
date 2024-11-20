from abc import ABC, abstractmethod

class SendDirectMessageListener(ABC):
    @abstractmethod
    def on_arrived(self) -> None:
        pass

    @abstractmethod
    def on_fault(self, error_message: str) -> None:
        pass
