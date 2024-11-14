from abc import ABC, abstractmethod
from typing import Collection

from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry

class HashMapChangedListener(ABC):
    @abstractmethod
    def on_added(self, protected_storage_entries: Collection["ProtectedStorageEntry"]) -> None:
        pass

    def on_removed(self, protected_storage_entries: Collection["ProtectedStorageEntry"]) -> None:
        # Often we are only interested in added data as there is no use case for remove
        pass
