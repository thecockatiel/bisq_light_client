from typing import TYPE_CHECKING
from collections.abc import Callable
from threading import Lock

from utils.concurrency import AtomicInt


if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
    from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
    from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
    from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray

class ProtectedDataStoreService:
    """Used for data which can be added and removed. ProtectedStorageEntry is used for verifying ownership."""
    
    def __init__(self):
        self.services: list["MapStoreService[PersistableEnvelope,ProtectedStorageEntry]"] = []
        self._lock = Lock()

    def add_service(self, service: "MapStoreService[PersistableEnvelope,ProtectedStorageEntry]") -> None:
        self.services.append(service)

    def remove_service(self, service: "MapStoreService[PersistableEnvelope,ProtectedStorageEntry]") -> None:
        if service in self.services:
            self.services.remove(service)

    def read_from_resources(self, post_fix: str, complete_handler: Callable[[], None]) -> None:
        if not self.services:
            complete_handler()
            return

        remaining = AtomicInt(len(self.services))
        
        def on_service_complete():
            nonlocal remaining
            remaining.decrement_and_get()
            if remaining.get() == 0:
                complete_handler()

        for service in self.services:
            service.read_from_resources(post_fix, on_service_complete)

    def read_from_resources_sync(self, post_fix: str) -> None:
        """Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code."""
        for service in self.services:
            service.read_from_resources_sync(post_fix)

    def get_map(self) -> dict["StorageByteArray", "ProtectedStorageEntry"]:
        result = {}
        for service in self.services:
            result.update(service.get_map())
        return result

    def put(self, hash: "StorageByteArray", entry: "ProtectedStorageEntry") -> None:
        for service in self.services:
            if service.can_handle(entry):
                service.put(hash, entry)

    def remove(self, hash_: "StorageByteArray", protected_storage_entry: "ProtectedStorageEntry") -> "ProtectedStorageEntry":
        result = None
        for service in self.services:
            if service.can_handle(protected_storage_entry):
                result = service.remove(hash_)
        return result
