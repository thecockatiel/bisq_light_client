from abc import ABC, abstractmethod
from collections.abc import Callable


class PersistedDataHost(ABC):
    @abstractmethod
    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        pass
