from abc import ABC
from typing import Collection, Generic, Optional, TypeVar
from bisq.common.protocol.persistable.persistable_envelope import (
    PersistableEnvelope,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from utils.concurrency import ThreadSafeDict

T = TypeVar("T", bound=PersistableNetworkPayload)


class PersistableNetworkPayloadStore(Generic[T], PersistableEnvelope, ABC):
    """Store for PersistableNetworkPayload map entries with it's data hash as key."""

    def __init__(self, collection: Optional[Collection[T]] = None) -> None:
        super().__init__()
        
        self.map: ThreadSafeDict["StorageByteArray", "PersistableNetworkPayload"] = {}
        
        if collection is not None:
            for payload in collection:
                self.map[StorageByteArray(payload.get_hash())] = payload
    
    def get_map(self):
        return self.map

    def __contains__(self, hash: "StorageByteArray") -> bool:
        return hash in self.map