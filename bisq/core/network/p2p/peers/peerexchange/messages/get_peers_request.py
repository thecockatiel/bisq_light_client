

from dataclasses import dataclass, field
from typing import Optional, Set

from bisq.core.common.capabilities import Capabilities
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.peers.peerexchange.messages.peer_exchange_message import PeerExchangeMessage
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.core.network.p2p.peers.peerexchange.peer import Peer
from bisq.core.network.p2p.node_address import NodeAddress
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class GetPeersRequest(NetworkEnvelope, PeerExchangeMessage, SendersNodeAddressMessage, SupportedCapabilitiesMessage):
    sender_node_address: NodeAddress
    nonce: int
    reported_peers: Set[Peer]
    supported_capabilities: Optional[Capabilities] = field(default=None)

    def __init__(self, sender_node_address: NodeAddress, nonce: int, reported_peers: Set[Peer], supported_capabilities: Optional[Capabilities] = None, message_version: int = Version.get_p2p_message_version()):
        if self.sender_node_address is None:
            raise ValueError("sender_node_address must not be null at GetPeersRequest")
        super().__init__(message_version)
        self.sender_node_address = sender_node_address
        self.nonce = nonce
        self.reported_peers = reported_peers
        self.supported_capabilities = supported_capabilities

    # PROTO BUFFER

    def to_proto_network_envelope(self):
        # We clone to avoid ConcurrentModificationExceptions
        clone = set(self.reported_peers)
        request = protobuf.GetPeersRequest(sender_node_address=self.sender_node_address.to_proto_message(),
                                           nonce=self.nonce,
                                           reported_peers=[peer.to_proto_message() for peer in clone])
        
        if self.supported_capabilities is not None:
            request.supported_capabilities = self.supported_capabilities.to_int_list()
        
        envelope = self.get_network_envelope_builder()
        envelope.get_peers_request = request
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.GetPeersRequest, message_version: int):
        return GetPeersRequest(
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            nonce=proto.nonce,
            reported_peers={Peer.from_proto(peer) for peer in proto.reported_peers},
            supported_capabilities=Capabilities.from_int_list(proto.supported_capabilities),
            message_version=message_version,
        )
