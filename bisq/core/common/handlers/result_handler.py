from abc import ABC, abstractmethod

class ResultHandler(ABC):
    @abstractmethod
    def handle_result(self) -> None:
        pass
