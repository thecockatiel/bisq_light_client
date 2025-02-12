
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar

from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.network.p2p.persistence.store_service import StoreService

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray

T = TypeVar(
    "T", bound=PersistableEnvelope
) 
R = TypeVar(
    "R", bound=PersistablePayload
) 

class MapStoreService(Generic[T, R], StoreService[T], ABC):
    """Handles persisted data which is stored in a map."""
    
    def __init__(self, storage_dir: Path, persistence_manager: "PersistenceManager[T]"):
        super().__init__(storage_dir, persistence_manager)
    
    # NOTE: Maybe TODO: I'm aware its not called map in python.
    @abstractmethod
    def get_map(self) -> dict["StorageByteArray", R]:
        pass
    
    @abstractmethod
    def can_handle(self, payload: R) -> bool:
        pass
    
    def put(self, hash: "StorageByteArray", payload: R):
        self.get_map()[hash] = payload
        self.request_persistence()
        
    def put_if_absent(self, hash: "StorageByteArray", payload: R):
        previous = self.get_map().get(hash, None)
        if previous is None:
            self.put(hash, payload)
        return previous
    
    def remove(self, hash: "StorageByteArray"):
        result = self.get_map().pop(hash, None)
        self.request_persistence()
        return result
    
    def __contains__(self, hash: "StorageByteArray"):
        return hash in self.get_map()