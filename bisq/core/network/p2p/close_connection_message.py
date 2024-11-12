from dataclasses import dataclass
from typing import TYPE_CHECKING

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
import proto.pb_pb2 as protobuf

@dataclass(kw_only=True)
class CloseConnectionMessage(NetworkEnvelope):
    reason: str

    # PROTO BUFFER

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.close_connection_message.CopyFrom(protobuf.CloseConnectionMessage(reason=self.reason))
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.CloseConnectionMessage, message_version: int) -> 'CloseConnectionMessage':
        return CloseConnectionMessage(reason=proto.reason, message_version=message_version)
