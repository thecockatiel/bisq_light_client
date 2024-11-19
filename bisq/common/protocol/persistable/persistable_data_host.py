from abc import ABC, abstractmethod
from typing import TypeVar
from collections.abc import Callable

from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope

T = TypeVar(
    "T", bound=PersistableEnvelope
)

class PersistedDataHost(ABC):
    @abstractmethod
    def read_persisted(self, complete_handler: Callable[[T], None]) -> None:
        pass