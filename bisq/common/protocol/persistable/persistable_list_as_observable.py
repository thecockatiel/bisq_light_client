from abc import ABC
from typing import Generic, Iterator, List, Optional, TypeVar
from collections.abc import Callable, Collection

from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from utils.data import ObservableList

T = TypeVar(
    "T", bound=PersistablePayload
)

class PersistableListAsObservable(PersistableList[T], ABC):
    
    def _create_list(self):
        return ObservableList[T]()
    
    def get_observable_list(self) -> ObservableList[T]:
        return self.list

    def add_listener(self, listener: Callable[['ObservableList', str, T], None]) -> ObservableList[T]:
        return self.get_observable_list().add_listener(listener)

    def remove_listener(self, listener: Callable[['ObservableList', str, T], None]):
        return self.get_observable_list().remove_listener(listener)