from abc import ABC
from typing import TypeVar
from collections.abc import Callable

from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from utils.data import ObservableChangeEvent, ObservableList

T = TypeVar(
    "T", bound=PersistablePayload
)

class PersistableListAsObservable(PersistableList[T], ABC):
    
    def _create_list(self):
        return ObservableList[T]()
    
    def get_observable_list(self) -> ObservableList[T]:
        return self.list

    def add_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]) -> ObservableList[T]:
        return self.get_observable_list().add_listener(listener)

    def remove_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]):
        return self.get_observable_list().remove_listener(listener)