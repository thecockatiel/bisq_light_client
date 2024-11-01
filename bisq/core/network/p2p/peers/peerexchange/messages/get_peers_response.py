from dataclasses import dataclass, field
from typing import Optional, Set
from bisq.core.common.capabilities import Capabilities
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.peers.peerexchange.messages.peer_exchange_message import PeerExchangeMessage
from bisq.core.network.p2p.peers.peerexchange.peer import Peer
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class GetPeersResponse(NetworkEnvelope, PeerExchangeMessage, SupportedCapabilitiesMessage):
    request_nonce: int
    reported_peers: Set[Peer]
    supported_capabilities: Optional[Capabilities] = field(default=None)

    def __init__(self, request_nonce: int, reported_peers: Set[Peer], supported_capabilities: Optional[Capabilities] = Capabilities.app, message_version: int = Version.get_p2p_message_version()):
        super().__init__(message_version)
        self.request_nonce = request_nonce
        self.reported_peers = reported_peers
        self.supported_capabilities = supported_capabilities

    def to_proto_network_envelope(self):
        clone = set(self.reported_peers)
        builder = protobuf.GetPeersResponse(
            request_nonce=self.request_nonce
        )

        for peer in clone:
            builder.reported_peers.add(peer.to_proto_message())

        if self.supported_capabilities:
            builder.supported_capabilities = Capabilities.to_int_list(self.supported_capabilities)

        envelope = self.get_network_envelope_builder()
        envelope.get_peers_response = builder
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.GetPeersResponse, message_version: int):
        reported_peers = set()
        for peer in proto.reported_peers:
            node_address = NodeAddress(host_name=peer.node_address.host_name, port=peer.node_address.port)
            capabilities = Capabilities.from_int_list(peer.supported_capabilities)
            reported_peers.add(Peer(node_address=node_address, supported_capabilities=capabilities))

        return GetPeersResponse(
            request_nonce=proto.request_nonce,
            reported_peers=reported_peers,
            supported_capabilities=Capabilities.from_int_list(proto.supported_capabilities),
            message_version=message_version
        )