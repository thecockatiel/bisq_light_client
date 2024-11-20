from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.peers.peer_manager import PeerManager
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import CapabilityRequiringPayload

logger = get_logger(__name__)

class CapabilityUtils:
    @staticmethod
    def capability_required_and_capability_not_supported(peers_node_address: "NodeAddress",
                                                       message: "NetworkEnvelope",
                                                       peer_manager: "PeerManager") -> bool:
        if not isinstance(message, CapabilityRequiringPayload):
            return False

        # We might have multiple entries of the same peer without the supportedCapabilities field set if we received
        # it from old versions, so we filter those.
        capabilities = peer_manager.find_peers_capabilities(peers_node_address)
        if capabilities is not None:
            result = capabilities.contains_all(message.get_required_capabilities())

            if not result:
                logger.warning("We don't send the message because the peer does not support the required capability. "
                          f"peersNodeAddress={peers_node_address}")

            return not result

        logger.warning("We don't have the peer in our persisted peers so we don't know their capabilities. "
                   f"We decide to not sent the msg. peersNodeAddress={peers_node_address}")
        return True
