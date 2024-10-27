from dataclasses import dataclass

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class CloseConnectionMessage(NetworkEnvelope):
    reason: str

    def __init__(self, reason: str, message_version: int = None):
        if message_version is None:
            message_version = Version.get_p2p_message_version()
        super().__init__(message_version)
        object.__setattr__(self, 'reason', reason)

    # PROTO BUFFER

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.close_connection_message = protobuf.CloseConnectionMessage(reason=self.reason)
        return envelope

    @classmethod
    def from_proto(cls, proto: protobuf.CloseConnectionMessage, message_version: int) -> 'CloseConnectionMessage':
        return cls(proto.reason, message_version)