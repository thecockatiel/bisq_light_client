from abc import ABC
from typing import Collection, Optional, TypeVar
from bisq.core.common.protocol.persistable.persistable_envelope import (
    PersistableEnvelope,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray

T = TypeVar("T", bound=PersistableNetworkPayload)


class PersistableNetworkPayloadStore(PersistableEnvelope, ABC):
    """Store for PersistableNetworkPayload map entries with it's data hash as key."""

    def __init__(self, collection: Optional[Collection[T]] = None) -> None:
        super().__init__()
        
        self.map: dict["StorageByteArray", "PersistableNetworkPayload"] = {}
        
        if collection is not None:
            for payload in collection:
                self.map[StorageByteArray(payload.get_hash())] = payload

    def __contains__(self, hash: "StorageByteArray") -> bool:
        return hash in self.map