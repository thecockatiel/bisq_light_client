from dataclasses import dataclass, field
from typing import Optional
from bisq.common.capabilities import Capabilities
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.peers.peerexchange.messages.peer_exchange_message import PeerExchangeMessage
from bisq.core.network.p2p.peers.peerexchange.peer import Peer
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
import proto.pb_pb2 as protobuf
from utils.data import raise_required

@dataclass
class GetPeersResponse(NetworkEnvelope, PeerExchangeMessage, SupportedCapabilitiesMessage):
    request_nonce: int = field(default_factory=raise_required)
    reported_peers: set[Peer] = field(default_factory=raise_required)
    supported_capabilities: Optional[Capabilities] = field(default=None)

    def to_proto_network_envelope(self):
        clone = set(self.reported_peers)
        builder = protobuf.GetPeersResponse(
            request_nonce=self.request_nonce
        )

        for peer in clone:
            builder.reported_peers.add(peer.to_proto_message())

        if self.supported_capabilities:
            builder.supported_capabilities.extend(Capabilities.to_int_list(self.supported_capabilities))

        envelope = self.get_network_envelope_builder()
        envelope.get_peers_response.CopyFrom(builder)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.GetPeersResponse, message_version: int):
        reported_peers = set()
        for peer in proto.reported_peers:
            node_address = NodeAddress(host_name=peer.node_address.host_name, port=peer.node_address.port)
            capabilities = Capabilities.from_int_list(peer.supported_capabilities)
            reported_peers.add(Peer(node_address=node_address, capabilities=capabilities))

        return GetPeersResponse(
            message_version=message_version,
            request_nonce=proto.request_nonce,
            reported_peers=reported_peers,
            supported_capabilities=Capabilities.from_int_list(proto.supported_capabilities),
        )