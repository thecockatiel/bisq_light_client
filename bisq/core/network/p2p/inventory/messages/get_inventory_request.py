from dataclasses import dataclass, field
from typing import Any
import pb_pb2 as protobuf
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from utils.data import raise_required


@dataclass
class GetInventoryRequest(NetworkEnvelope):
    version: str = field(default_factory=raise_required)

    def to_proto_network_envelope(self) -> "protobuf.NetworkEnvelope": 
        envelope = self.get_network_envelope_builder()
        envelope.get_inventory_request.CopyFrom(
            protobuf.GetInventoryRequest(version=self.version)
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.GetInventoryRequest, message_version: int) -> "GetInventoryRequest":
        return GetInventoryRequest(
            message_version=message_version,
            version=proto.version, 
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GetInventoryRequest):
            return False
        return self.version == other.version

    def __str__(self) -> str:
        return f"GetInventoryRequest(version={self.version})"
