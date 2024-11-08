from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bisq.core.common.protocol.network.network_payload import NetworkPayload
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload 

if TYPE_CHECKING:
    import proto.pb_pb2 as protobuf
    from bisq.core.common.protocol.proto_resolver import ProtoResolver

class PersistableNetworkPayload(NetworkPayload, PersistablePayload, ABC):
    """
    Marker interface for NetworkPayload which gets persisted in PersistableNetworkPayloadMap.
    We store it as a list in PB to keep storage size small (map would use hash as key which is in data object anyway).
    Not using a map also give more tolerance with data structure changes.
    This data structure does not use a verification of the owners signature. ProtectedStoragePayload is used if that is required.
    Currently we use it only for the AccountAgeWitness and TradeStatistics data.
    It is used for an append only data storage because removal would require owner verification.
    """

    @staticmethod
    def from_proto(payload: "protobuf.PersistableNetworkPayload", resolver: "ProtoResolver"):
        return resolver.from_proto(payload)

    @abstractmethod
    def to_proto_message(self) -> "protobuf.PersistableNetworkPayload":
        pass

    @abstractmethod
    def get_hash(self) -> bytes:
        """Hash which will be used as key in the in-memory hashMap"""
        pass

    @abstractmethod
    def verify_hash_size(self) -> bool:
        pass