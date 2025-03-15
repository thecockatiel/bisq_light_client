from concurrent.futures import Future
from datetime import timedelta
import random
from typing import TYPE_CHECKING, Optional
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.dao.governance.blindvote.network.messages.republish_governance_data_request import (
    RepublishGovernanceDataRequest,
)


if TYPE_CHECKING:
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.node_address import NodeAddress

logger = get_logger(__name__)


class RepublishGovernanceDataHandler:
    """
    Responsible for sending a RepublishGovernanceDataRequest to full nodes.
    Processing of RepublishBlindVotesRequests at full nodes is done in the FullNodeNetworkService.
    """

    TIMEOUT_SEC = 120

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        seed_nodes_repository: "SeedNodeRepository",
    ):
        self._network_node = network_node
        self._peer_manager = peer_manager
        self._seed_node_addresses = set(seed_nodes_repository.get_seed_node_addresses())
        self._stopped = False
        self._timeout_timer: Optional[Timer] = None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_republish_request(self):
        # First try if we have a seed node in our connections. All seed nodes are full nodes.
        if not self._stopped:
            self._connect_to_next_node()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _send_republish_request(self, node_address: "NodeAddress"):
        republish_governance_data_request = RepublishGovernanceDataRequest()
        if self._timeout_timer is None:
            self._timeout_timer = UserThread.run_after(
                lambda: self._handle_timeout(node_address),
                timedelta(seconds=RepublishGovernanceDataHandler.TIMEOUT_SEC),
            )

        logger.info(f"Sending republishGovernanceDataRequest to peer {node_address}.")
        future = self._network_node.send_message(
            node_address, republish_governance_data_request
        )
        future.add_done_callback(lambda f: self._handle_send_result(f, node_address))

    def _handle_timeout(self, node_address: "NodeAddress"):
        # setup before sending to avoid race conditions
        if not self._stopped:
            logger.warning(
                f"A timeout occurred while sending republishGovernanceDataRequest to nodeAddress: {node_address}"
            )
            self._connect_to_next_node()
        else:
            logger.warning(
                "We have stopped already. We ignore that timeoutTimer.run call."
                "Might be caused by a previous networkNode.sendMessage.onFailure."
            )

    def _handle_send_result(self, future: "Future", node_address: "NodeAddress"):
        try:
            future.result()
            if not self._stopped:
                logger.info(
                    f"Sending of RepublishGovernanceDataRequest message to peer {node_address.get_full_address()} succeeded."
                )
                self._stop()
            else:
                logger.debug(
                    "We have stopped already. We ignore that networkNode.sendMessage.onSuccess call."
                    "Might be caused by a previous timeout."
                )
        except Exception as e:
            if not self._stopped:
                logger.info(
                    f"Sending republishGovernanceDataRequest to {node_address} failed. Exception: {e}"
                )
                self._handle_fault(node_address)
                self._connect_to_next_node()
            else:
                logger.debug(
                    "We have stopped already. We ignore that networkNode.sendMessage.onFailure call."
                    "Might be caused by a previous timeout."
                )

    def _connect_to_next_node(self):
        # First we try our connected seed nodes
        connection_to_seed_node_optional = next(
            (
                conn
                for conn in self._network_node.get_confirmed_connections()
                if self._peer_manager.is_seed_node(conn.peers_node_address)
            ),
            None,
        )
        if (
            connection_to_seed_node_optional
            and connection_to_seed_node_optional.peers_node_address
        ):
            node_address = connection_to_seed_node_optional.peers_node_address
            self._send_republish_request(node_address)
        else:
            # If connected seed nodes did not confirm receipt of message we try next seed node from seed_node_addresses
            seed_node_list = [
                addr
                for addr in self._seed_node_addresses
                if self._peer_manager.is_seed_node(addr)
                and not self._peer_manager.is_self(addr)
            ]
            random.shuffle(seed_node_list)

            if seed_node_list:
                node_address = seed_node_list.pop(0)
                self._seed_node_addresses.discard(node_address)
                self._send_republish_request(node_address)
            else:
                logger.warning(
                    "No more seed nodes available. We try any of our other peers."
                )
                self._connect_to_any_full_node()

    # JAVA TODO support also lite nodes
    def _connect_to_any_full_node(self):
        required = Capabilities([Capability.DAO_FULL_NODE])

        live_peers = [
            peer
            for peer in self._peer_manager.get_live_peers()
            if peer.capabilities.contains_all(required)
        ]

        if not live_peers:
            live_peers = [
                peer
                for peer in self._peer_manager.get_reported_peers()
                if peer.capabilities.contains_all(required)
            ]

        if not live_peers:
            live_peers = [
                peer
                for peer in self._peer_manager.get_persisted_peers()
                if peer.capabilities.contains_all(required)
            ]

        if live_peers:
            # We avoid the complexity to maintain the results of all our peers and to iterate all until we find a good peer,
            # but we prefer simplicity with the risk that we don't get the data so we request from max 4 peers in parallel
            # assuming that at least one will republish and therefore we should receive all data.
            selected_peers = random.sample(live_peers, min(len(live_peers), 4))
            for peer in selected_peers:
                self._send_republish_request(peer.node_address)
        else:
            logger.warning("No other nodes found. We try again in 60 seconds.")
            UserThread.run_after(self._connect_to_next_node, timedelta(seconds=60))

    def _handle_fault(self, node_address: "NodeAddress"):
        self._peer_manager.handle_connection_fault(node_address=node_address)

    def _stop(self):
        self._stopped = True
        self._stop_timeout_timer()

    def _stop_timeout_timer(self):
        if self._timeout_timer is not None:
            self._timeout_timer.stop()
            self._timeout_timer = None
