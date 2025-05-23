from dataclasses import dataclass, field
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.peers.keepalive.messages.keep_alive_message import KeepAliveMessage
import pb_pb2 as protobuf
from utils.data import raise_required


@dataclass
class Pong(NetworkEnvelope, KeepAliveMessage):
    request_nonce: int = field(default_factory=raise_required)

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.pong.CopyFrom(protobuf.Pong(request_nonce=self.request_nonce))
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.Pong, message_version: int) -> "Pong":
        return Pong(message_version=message_version, request_nonce=proto.request_nonce)
