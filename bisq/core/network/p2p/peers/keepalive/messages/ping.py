from dataclasses import dataclass, field
from bisq.common.protocol.network.network_envelope import NetworkEnvelope 
from bisq.core.network.p2p.peers.keepalive.messages.keep_alive_message import KeepAliveMessage
import proto.pb_pb2 as protobuf


@dataclass(kw_only=True)
class Ping(NetworkEnvelope, KeepAliveMessage):
    nonce: int
    last_round_trip_time: int = field(default=0)

    # Convert the Ping object to a protobuf NetworkEnvelope.
    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.ping.CopyFrom(
            protobuf.Ping(
                nonce=self.nonce, last_round_trip_time=self.last_round_trip_time
            )
        )
        return envelope

    # Create a Ping object from a protobuf Ping message.
    @staticmethod
    def from_proto(proto: protobuf.Ping, message_version: int) -> "Ping":
        return Ping(
            message_version=message_version,
            nonce=proto.nonce,
            last_round_trip_time=proto.last_round_trip_time,
        )
