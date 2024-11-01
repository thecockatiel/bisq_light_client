from dataclasses import dataclass
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.peers.keepalive.keep_alive_message import KeepAliveMessage
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class Ping(NetworkEnvelope, KeepAliveMessage):
    nonce: int
    last_round_trip_time: int

    # Convert the Ping object to a protobuf NetworkEnvelope.
    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.ping.CopyFrom(protobuf.Ping(nonce=self.nonce, last_round_trip_time=self.last_round_trip_time))
        return envelope

    # Create a Ping object from a protobuf Ping message.
    @staticmethod
    def from_proto(proto: protobuf.Ping, message_version: int) -> 'Ping':
        return Ping(message_version,
                    proto.nonce,
                    proto.last_round_trip_time)