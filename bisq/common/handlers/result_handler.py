from abc import ABC, abstractmethod
from collections.abc import Callable

class ResultHandler(Callable[[], None],ABC):
    @abstractmethod
    def handle_result(self) -> None:
        pass

    def __call__(self) -> None:
        self.handle_result()