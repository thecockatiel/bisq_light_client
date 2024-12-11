from abc import ABC
from typing import Generic, Iterator, List, Optional, TypeVar
from collections.abc import Collection

from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload

T = TypeVar(
    "T", bound=PersistablePayload
)

class PersistableList(Generic[T], PersistableEnvelope, ABC):
    def _create_list(self) -> List[T]:
        return []
    
    def __init__(self, collection: Optional[Collection[T]] = None) -> None:
        super().__init__()
        self.list = self._create_list()
        if collection:
            self.set_all(collection)
    
    def set_all(self, collection: Collection[T]) -> None:
        self.list.clear()
        self.list.extend(collection)
        
    def append(self, item: T) -> bool:
        if item not in self.list:
            self.list.append(item)
            return True
        return False
        
    def remove(self, item: T) -> bool:
        if item in self.list:
            self.list.remove(item)
            return True
        return False
        
    def is_empty(self) -> bool:
        return len(self.list) == 0
        
    def clear(self) -> None:
        self.list.clear()
        
            
    def __getitem__(self, index: int) -> T: 
        return self.list[index]
    
    def __setitem__(self, index: int, value: T) -> None: 
        self.list[index] = value
        
    def __len__(self) -> int:
        return len(self.list)
    
    def __iter__(self) -> Iterator[T]:
        return iter(self.list)

    def __contains__(self, item: T):
        return item in self.list
    
    def __str__(self) -> str:
        return str(self.list)