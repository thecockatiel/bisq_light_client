from dataclasses import dataclass
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.peers.keepalive.keep_alive_message import KeepAliveMessage
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class Pong(NetworkEnvelope, KeepAliveMessage):
    request_nonce: int

    def __init__(self, request_nonce, message_version=Version.get_p2p_message_version()):
        super().__init__(message_version)
        self.request_nonce = request_nonce

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.pong = protobuf.Pong(request_nonce=self.request_nonce)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.Pong, message_version: int) -> 'Pong':
        return Pong(proto.request_nonce, message_version)