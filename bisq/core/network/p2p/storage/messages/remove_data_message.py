from dataclasses import dataclass, field

from bisq.core.network.p2p.storage.broadcast_message import BroadcastMessage
from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver    

@dataclass(frozen=True)
class RemoveDataMessage(BroadcastMessage):
    protected_storage_entry: ProtectedStorageEntry
    message_version: int = field(default_factory=Version.get_p2p_message_version)

    # PROTO BUFFER
    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.remove_data_message = protobuf.RemoveDataMessage(
            protected_storage_entry = self.to_proto_message()
        )
        return envelope

    @staticmethod
    def from_proto(proto: 'protobuf.RemoveDataMessage', resolver: 'NetworkProtoResolver', message_version: int):
        return RemoveDataMessage(ProtectedStorageEntry.from_proto(proto.protected_storage_entry, resolver), message_version)