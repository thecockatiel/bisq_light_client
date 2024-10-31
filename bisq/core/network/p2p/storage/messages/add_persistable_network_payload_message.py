from bisq.core.network.p2p.storage.broadcast_message import BroadcastMessage 
from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf
from dataclasses import dataclass, field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver

@dataclass(frozen=True)
class AddPersistableNetworkPayloadMessage(BroadcastMessage):
    persistable_network_payload: 'PersistableNetworkPayload'
    message_version: int = field(default_factory=lambda: Version.get_p2p_message_version())

    def __post_init__(self):
        if not isinstance(self.persistable_network_payload, PersistableNetworkPayload):
            raise ValueError("persistable_network_payload must be an instance of PersistableNetworkPayload")

    # PROTO BUFFER

    def to_proto_network_envelope(self):
        envelope = self.get_network_envelope_builder()
        envelope.add_persistable_network_payload_message = protobuf.AddPersistableNetworkPayloadMessage(payload=self.persistable_network_payload.to_proto_message())
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.AddPersistableNetworkPayloadMessage, resolver: 'NetworkProtoResolver', message_version: int):
        return AddPersistableNetworkPayloadMessage(
            persistable_network_payload=resolver.from_proto_persistable_network(proto.payload),
            message_version=message_version
        )