from dataclasses import dataclass

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
import proto.pb_pb2 as protobuf
import bisq.core.common.version as Version

@dataclass(frozen=True)
class CloseConnectionMessage(NetworkEnvelope):
    reason: str

    def __init__(self, reason: str, message_version: int = Version.get_p2p_message_version()): 
        super().__init__(message_version)
        self.reason = reason

    # PROTO BUFFER

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.close_connection_message.CopyFrom(protobuf.CloseConnectionMessage(reason=self.reason))
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.CloseConnectionMessage, message_version: int) -> 'CloseConnectionMessage':
        return CloseConnectionMessage(proto.reason, message_version)
