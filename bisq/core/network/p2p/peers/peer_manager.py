from abc import ABC, abstractmethod
from collections.abc import Callable
from bisq.common.setup.log_setup import get_ctx_logger
import random
from datetime import timedelta
from typing import Optional, TYPE_CHECKING

from bisq.common.capability import Capability
from bisq.common.clock_watcher_listener import ClockWatcherListener
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.inbound_connection import InboundConnection
from bisq.core.network.p2p.network.peer_type import PeerType
from bisq.core.network.p2p.network.rule_violation import RuleViolation
from bisq.core.network.p2p.peers.peerexchange.peer_list import PeerList
from utils.concurrency import ThreadSafeSet
from utils.preconditions import check_argument
from utils.time import get_time_ms
from bisq.common.capabilities import Capabilities
from bisq.core.network.p2p.peers.peerexchange.peer import Peer


if TYPE_CHECKING:
    from bisq.common.clock_watcher import ClockWatcher
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.node_address import NodeAddress



class PeerManager(ConnectionListener, PersistedDataHost):
    # Constants
    CHECK_MAX_CONN_DELAY_SEC = 10
    # Use a long delay as the bootstrapping peer might need a while until it knows its onion address
    REMOVE_ANONYMOUS_PEER_SEC = 240

    MAX_REPORTED_PEERS = 1000
    MAX_PERSISTED_PEERS = 500
    # max age for reported peers is 14 days
    MAX_AGE = int(timedelta(days=14).total_seconds() * 1000)  # in milliseconds
    # Age of what we consider connected peers still as live peers
    MAX_AGE_LIVE_PEERS = int(
        timedelta(minutes=30).total_seconds() * 1000
    )  # in milliseconds
    PRINT_REPORTED_PEERS_DETAILS = True

    class Listener(ABC):
        @abstractmethod
        def on_all_connections_lost(self_):
            pass

        @abstractmethod
        def on_new_connection_after_all_connections_lost(self_):
            pass

        @abstractmethod
        def on_awake_from_standby(self_):
            pass

    def __init__(
        self,
        network_node: "NetworkNode",
        seed_node_repository: "SeedNodeRepository",
        clock_watcher: "ClockWatcher",
        persistence_manager: "PersistenceManager[PeerList]",
        max_connections: int,
    ):
        self.logger = get_ctx_logger(__name__)
        self._shut_down_requested = False
        self._num_on_connections = 0

        self._network_node = network_node
        self._clock_watcher = clock_watcher
        self._seed_node_addresses = ThreadSafeSet["NodeAddress"](
            seed_node_repository.get_seed_node_addresses()
        )
        self._persistence_manager = persistence_manager
        self._listeners = ThreadSafeSet["PeerManager.Listener"]()

        # Persistable peerList
        self._peer_list = PeerList()

        # Peers we got reported from other peers
        self._reported_peers = ThreadSafeSet["Peer"]()
        # Most recent peers with activity date of last 30 min.
        self._latest_live_peers = ThreadSafeSet["Peer"]()

        self._check_max_connections_timer: Timer = None
        self._stopped = False
        self._lost_all_connections = False
        self.set_connection_limits(max_connections)

        self._peak_num_connections = 0
        self._num_all_connections_lost_events = 0

        self._persistence_manager.initialize(
            self._peer_list, PersistenceManagerSource.PRIVATE_LOW_PRIO
        )
        self._network_node.add_connection_listener(self)

        # we check if app was idle for more then 5 sec.
        class Listener(ClockWatcherListener):
            def on_second_tick(self_):
                pass

            def on_minute_tick(self_):
                pass

            def on_awake_from_standby(self_, missed_ms):
                # We got probably stopped set to true when we got a longer interruption (e.g. lost all connections),
                # now we get awake again, so set stopped to false.
                self._stopped = False
                for listener in self._listeners:
                    listener.on_awake_from_standby()

        self._clock_watcher_listener = Listener()
        self._clock_watcher.add_listener(self._clock_watcher_listener)

        self._print_statistics_timer = UserThread.run_periodically(
            lambda: self._print_statistics(), timedelta(minutes=60)
        )

    @property
    def reported_peers(self):
        return self._reported_peers

    @property
    def min_connections(self):
        return self._min_connections

    @property
    def peak_num_connections(self):
        return self._peak_num_connections

    @property
    def num_all_connections_lost_events(self):
        return self._num_all_connections_lost_events

    # Modify this to change the relationships between connection limits.
    # maxConnections default 12
    def set_connection_limits(self, max_connections: int):
        self._max_connections = max_connections  # app node 12; seedNode 20
        self._min_connections = max(
            1, round(max_connections * 0.7)
        )  # app node  8; seedNode 14
        self._out_bound_peer_trigger = max(
            4, round(max_connections * 1.3)
        )  # app node 16; seedNode 26
        self._initial_data_exchange_trigger = max(
            8, round(max_connections * 1.7)
        )  # app node 20; seedNode 34
        self._max_connections_absolute = max(
            12, round(max_connections * 2.5)
        )  # app node 30; seedNode 50

    def shut_down(self):
        self._shut_down_requested = True
        self._network_node.remove_connection_listener(self)
        self._clock_watcher.remove_listener(self._clock_watcher_listener)
        self._stop_check_max_connections_timer()
        if self._print_statistics_timer:
            self._print_statistics_timer.stop()
            self._print_statistics_timer = None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        self._persistence_manager.read_persisted(
            lambda persisted: (
                self._peer_list.set_all(persisted.set),
                complete_handler(),
            ),
            complete_handler,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection: "Connection"):
        connection.connection_state.is_seed_node = self.is_seed_node(connection.peers_node_address)

        self._do_housekeeping()

        self._num_on_connections += 1

        if self._lost_all_connections:
            self._lost_all_connections = False
            self._stopped = False
            self.logger.info(
                "\n------------------------------------------------------------\n"
                + f"Established a new connection from/to {connection.peers_node_address} after all connections lost.\n"
                + "------------------------------------------------------------"
            )
            for listener in self._listeners:
                listener.on_new_connection_after_all_connections_lost()

        peer_address = connection.peers_node_address
        if peer_address:
            peer = self.find_peer(peer_address)
            if peer:
                peer.on_connection()

    def on_disconnect(self, close_connection_reason, connection):
        self.logger.debug(
            f"on_disconnect called: node_address={connection.peers_node_address}, reason={close_connection_reason}"
        )
        self.handle_connection_fault(connection=connection)

        previous_lost_all_connections = self._lost_all_connections
        self._lost_all_connections = not self._network_node.get_all_connections()

        # At start-up we ignore if we would lose a connection and would fall back to no connections
        if self._lost_all_connections and self._num_on_connections > 2:
            self._stopped = True

            if not self._shut_down_requested:
                if not previous_lost_all_connections:
                    # If we enter to 'All connections lost' we count the event.
                    self._num_all_connections_lost_events += 1
                self.logger.warning(
                    "\n------------------------------------------------------------\n"
                    + "All connections lost\n"
                    + "------------------------------------------------------------"
                )
                for listener in self._listeners:
                    listener.on_all_connections_lost()

        self.maybe_remove_banned_peer(close_connection_reason, connection)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Connection
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def has_sufficient_connections(self) -> bool:
        return (
            len(self._network_node.get_confirmed_connections()) >= self._min_connections
        )

    # Checks if that connection has the peers node address
    def is_confirmed(self, node_address: "NodeAddress") -> bool:
        return (
            node_address
            in self._network_node.get_node_addresses_of_confirmed_connections()
        )

    def handle_connection_fault(
        self,
        *,
        node_address: "NodeAddress" = None,
        connection: Optional["Connection"] = None,
    ):
        if connection:
            node_address = connection.peers_node_address
            if not node_address:
                return  # TODO: java sanity check
        elif node_address:
            connection = None
        else:
            raise ValueError("Either node_address or connection must be provided")

        do_remove_persisted_peer = False
        self._remove_reported_peer_address(node_address)
        persisted_peer = self._find_persisted_peer(node_address)
        if persisted_peer:
            persisted_peer.on_disconnect()
            do_remove_persisted_peer = (
                persisted_peer.too_many_failed_connection_attempts()
            )
        rule_violation = connection and connection.rule_violation is not None
        do_remove_persisted_peer = do_remove_persisted_peer or rule_violation

        if do_remove_persisted_peer:
            self._remove_persisted_peer_address(node_address)
        else:
            self._remove_too_old_persisted_peers()

    def is_connection_seed_node(self, connection: "Connection") -> bool:
        node_address = connection.peers_node_address
        if node_address:
            return self.is_seed_node(node_address)
        return False

    def is_self(self, node_address: "NodeAddress") -> bool:
        return node_address == self._network_node.node_address_property.value

    def is_seed_node(self, node_address: "NodeAddress") -> bool:
        return (
            node_address in self._seed_node_addresses
            if node_address is not None
            else False
        )

    def is_peer_banned(
        self, reason: "CloseConnectionReason", connection: "Connection"
    ) -> bool:
        return (
            reason == CloseConnectionReason.PEER_BANNED
            and connection.peers_node_address is not None
        )

    def maybe_remove_banned_peer(
        self, close_connection_reason: "CloseConnectionReason", connection: "Connection"
    ):
        if self.is_peer_banned(close_connection_reason, connection):
            node_address = connection.peers_node_address
            if node_address:
                self._seed_node_addresses.discard(node_address)
                self._remove_persisted_peer_address(node_address)
                self._remove_reported_peer_address(node_address)

    def maybe_reset_num_all_connections_lost_events(self):
        if self._network_node.get_all_connections():
            self._num_all_connections_lost_events = 0

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Peer
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def find_peer(self, node_address: "NodeAddress") -> Optional["Peer"]:
        return next(
            (
                peer
                for peer in self.get_all_peers()
                if peer.node_address == node_address
            ),
            None,
        )

    def get_all_peers(self):
        return (
            self.get_live_peers()
            .union(self.get_persisted_peers())
            .union(self._reported_peers)
        )

    def get_persisted_peers(self):
        return self._peer_list.set

    # TODO: replace usages with prop access
    def get_reported_peers(self):
        return self._reported_peers

    def add_to_reported_peers(
        self,
        reported_peers_to_add: set["Peer"],
        connection: "Connection",
        capabilities: "Capabilities",
    ):
        self._apply_capabilities(connection, capabilities)

        peers = {
            peer
            for peer in reported_peers_to_add
            if not self.is_self(peer.node_address)
        }

        self._print_new_reported_peers(peers)

        # We check if the reported msg is not violating our rules
        if len(peers) <= (
            PeerManager.MAX_REPORTED_PEERS + self._max_connections_absolute + 10
        ):
            self._reported_peers.update(peers)
            self._purge_reported_peers_if_exceeds()

            self.get_persisted_peers().update(peers)
            self._purge_persisted_peers_if_exceeds()
            self._request_persistence()

            self._print_reported_peers()
        else:
            # If a node is trying to send too many list we treat it as rule violation.
            # Reported list include the connected list. We use the max value and give some extra headroom.
            # Will trigger a shutdown after 2nd time sending too much
            connection.report_invalid_request(
                RuleViolation.TOO_MANY_REPORTED_PEERS_SENT
            )

    # Delivers the live peers from the last 30 min (MAX_AGE_LIVE_PEERS)
    # We include older peers to avoid risks for network partitioning
    def get_live_peers(self, excluded_node_address: Optional["NodeAddress"] = None):
        old_num_latest_live_peers = len(self._latest_live_peers)

        peers = self._latest_live_peers.copy()

        current_live_peers = {
            peer
            for peer in self._get_connected_reported_peers()
            if not self.is_seed_node(peer)
            and peer.node_address != excluded_node_address
        }
        peers.update(current_live_peers)

        max_age = get_time_ms() - PeerManager.MAX_AGE_LIVE_PEERS
        self._latest_live_peers.clear()
        recent_peers = {peer for peer in peers if peer.date > max_age}
        self._latest_live_peers.update(recent_peers)

        if old_num_latest_live_peers != len(self._latest_live_peers):
            self.logger.info(f"Num of latest_live_peers={len(self._latest_live_peers)}")
        return self._latest_live_peers

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Capabilities
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def peer_has_capability(
        self, node_address: "NodeAddress", capability: "Capability"
    ) -> bool:
        capabilities = self.find_peers_capabilities(node_address)
        return capability in capabilities if capabilities is not None else False

    def find_peers_capabilities(
        self, node_address: "NodeAddress"
    ) -> Optional["Capabilities"]:
        # We look up first our connections as that is our own data. If not found there we look up the peers which
        # include reported peers.
        capabilities = self._network_node.find_peers_capabilities(node_address)
        if capabilities and not capabilities.is_empty():
            return capabilities

        # Reported peers are not trusted data. We could get capabilities which miss the
        # peers real capability or we could get maliciously altered capabilities telling us the peer supports a
        # capability which is in fact not supported. This could lead to connection loss as we might send data not
        # recognized by the peer. As we register a listener on connection if we don't have set the capability from our
        # own sources we would get it fixed as soon we have a connection with that peer, rendering such an attack
        # inefficient.
        # Also this risk is only for not updated peers, so in case that would be abused for an
        # attack all users have a strong incentive to update ;-).
        for peer in self.get_all_peers():
            if peer.node_address == node_address:
                return peer.capabilities
        return None

    def _apply_capabilities(
        self, connection: "Connection", new_capabilities: "Capabilities"
    ):
        if new_capabilities is None or new_capabilities.is_empty():
            return

        node_address = connection.peers_node_address
        if node_address:
            for peer in self.get_all_peers():
                if peer.node_address == node_address and peer.capabilities.has_less(
                    new_capabilities
                ):
                    peer.capabilities = new_capabilities
        self._request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Housekeeping
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _do_housekeeping_task(self):
        self._stop_check_max_connections_timer()
        if not self._stopped:
            all_connections = self._network_node.get_all_connections()
            size = len(all_connections)
            self._peak_num_connections = max(self._peak_num_connections, size)

            self._remove_anonymous_peers()
            self._remove_too_old_reported_peers()
            self._remove_too_old_persisted_peers()
            self.check_max_connections()
        else:
            self.logger.debug(
                "We have stopped already. We ignore that check_max_connections_timer call."
            )

    def _do_housekeeping(self):
        if self._check_max_connections_timer is None:
            self._print_connected_peers()
            self._check_max_connections_timer = UserThread.run_after(
                self._do_housekeeping_task,
                timedelta(seconds=PeerManager.CHECK_MAX_CONN_DELAY_SEC),
            )

    def check_max_connections(self) -> bool:
        all_connections = self._network_node.get_all_connections()
        size = len(all_connections)
        self.logger.info(
            f"We have {size} connections open. Our limit is {self._max_connections}"
        )

        if size <= self._max_connections:
            self.logger.debug(
                f"We have not exceeded the maxConnections limit of {size} "
                "so don't need to close any connections."
            )
            return False

        self.logger.info(
            "We have too many connections open. "
            "Lets try first to remove the inbound connections of type PEER."
        )
        candidates = sorted(
            [
                conn
                for conn in all_connections
                if isinstance(conn, InboundConnection)
                and conn.connection_state.peer_type == PeerType.PEER
            ],
            key=lambda x: x.statistic.last_activity_timestamp,
        )

        if not candidates:
            self.logger.info(
                "No candidates found. We check if we exceed our "
                f"out_bound_peer_trigger of {self._out_bound_peer_trigger}"
            )
            if size <= self._out_bound_peer_trigger:
                self.logger.info(
                    f"We have not exceeded out_bound_peer_trigger of {self._out_bound_peer_trigger} "
                    "so don't need to close any connections"
                )
                return False

            self.logger.info(
                f"We have exceeded out_bound_peer_trigger of {self._out_bound_peer_trigger}. "
                "Lets try to remove outbound connection of type PEER."
            )
            candidates = sorted(
                [
                    conn
                    for conn in all_connections
                    if conn.connection_state.peer_type == PeerType.PEER
                ],
                key=lambda x: x.statistic.last_activity_timestamp,
            )

            if not candidates:
                self.logger.info(
                    "No candidates found. We check if we exceed our "
                    f"initial_data_exchange_trigger of {self._initial_data_exchange_trigger}"
                )
                if size <= self._initial_data_exchange_trigger:
                    self.logger.info(
                        f"We have not exceeded initial_data_exchange_trigger of {self._initial_data_exchange_trigger} "
                        "so don't need to close any connections"
                    )
                    return False

                self.logger.info(
                    f"We have exceeded initial_data_exchange_trigger of {self._initial_data_exchange_trigger}. "
                    "Lets try to remove the oldest INITIAL_DATA_EXCHANGE connection"
                )
                candidates = sorted(
                    [
                        conn
                        for conn in all_connections
                        if conn.connection_state.peer_type
                        == PeerType.INITIAL_DATA_EXCHANGE
                    ],
                    key=lambda x: x.connection_state.last_initial_data_msg_timestamp,
                )

                if not candidates:
                    self.logger.info(
                        "No candidates found. We check if we exceed our "
                        f"max_connections_absolute of {self._max_connections_absolute}"
                    )
                    if size <= self._max_connections_absolute:
                        self.logger.info(
                            f"We have not exceeded max_connections_absolute limit of {self._max_connections_absolute} "
                            "so don't need to close any connections"
                        )
                        return False
                    self.logger.info(
                        "We reached abs. max. connections. Lets try to remove ANY connection."
                    )
                    candidates = sorted(
                        all_connections,
                        key=lambda x: x.statistic.last_activity_timestamp,
                    )

        if candidates:
            connection = candidates.pop(0)
            self.logger.info(
                f"check_max_connections: Num candidates (inbound/peer) for shut down={len(candidates)}. We close oldest connection to peer {connection.peers_node_address}"
            )
            if not connection.stopped:
                connection.shut_down(
                    CloseConnectionReason.TOO_MANY_CONNECTIONS_OPEN,
                    lambda: UserThread.run_after(
                        self.check_max_connections, timedelta(milliseconds=100)
                    ),
                )
                return True

        self.logger.info(
            "No candidates found to remove. "
            f"size={size}, all_connections={all_connections}"
        )
        return False

    def _remove_anonymous_peers(self):
        for connection in self._network_node.get_all_connections():
            if (
                not connection.peers_node_address
                and connection.connection_state.peer_type == PeerType.PEER
            ):
                # java TODO we keep a potentially dead connection in memory for too long...
                # We give 240 seconds delay and check again if still no address is set
                # Keep the delay long as we don't want to disconnect a peer in case we are a seed node just
                # because he needs longer for the HS publishing
                UserThread.run_after(
                    lambda c=connection: self._close_anonymous_connection(c),
                    timedelta(seconds=PeerManager.REMOVE_ANONYMOUS_PEER_SEC),
                )

    def _close_anonymous_connection(self, connection: "Connection"):
        if not connection.stopped.get() and not connection.peers_node_address:
            self.logger.info(
                "removeAnonymousPeers: We close the connection as the peer address is still unknown. "
                f"Peer: {connection.peers_node_address}"
            )
            connection.shut_down(CloseConnectionReason.UNKNOWN_PEER_ADDRESS)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Reported peers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _remove_reported_peer(self, reported_peer: "Peer"):
        self._reported_peers.discard(reported_peer)
        self._print_reported_peers()

    def _remove_reported_peer_address(self, node_address: "NodeAddress"):
        if not node_address:
            return
        peer = next(
            (
                peer
                for peer in self._reported_peers
                if peer.node_address == node_address
            ),
            None,
        )
        if peer:
            self._remove_reported_peer(peer)

    def _remove_too_old_reported_peers(self):
        old_peers = {
            peer
            for peer in self._reported_peers
            if get_time_ms() - peer.date > PeerManager.MAX_AGE
        }
        for peer in old_peers:
            self._remove_reported_peer(peer)

    def _purge_reported_peers_if_exceeds(self):
        size = len(self._reported_peers)
        if size > PeerManager.MAX_REPORTED_PEERS:
            self.logger.info(
                f"We have already {size} reported peers which exceeds our limit of {PeerManager.MAX_REPORTED_PEERS}."
                + "We remove random peers from the reported peers list."
            )
            # we randomly remove peers
            peers_to_remove = random.sample(
                list(self._reported_peers), size - PeerManager.MAX_REPORTED_PEERS
            )
            for peer in peers_to_remove:
                self._remove_reported_peer(peer)
        else:
            self.logger.trace(
                f"No need to purge reported peers.\n\tWe don't have more then {PeerManager.MAX_REPORTED_PEERS} reported peers yet."
            )

    def _print_reported_peers(self):
        if self._reported_peers:
            if PeerManager.PRINT_REPORTED_PEERS_DETAILS:
                result = (
                    "\n\n------------------------------------------------------------\n"
                    "Collected reported peers:"
                )

                for peer in self._reported_peers:
                    result += f"\n{peer}"

                result += (
                    "\n------------------------------------------------------------\n"
                )
                self.logger.trace(result)
            self.logger.debug(f"Number of reported peers: {len(self._reported_peers)}")

    def _print_new_reported_peers(self, reported_peers: set["Peer"]):
        if PeerManager.PRINT_REPORTED_PEERS_DETAILS:
            peers_details = "\n\t".join(str(peer) for peer in reported_peers)
            self.logger.trace(f"We received new reportedPeers:\n\t{peers_details}")
        self.logger.debug(f"Number of new arrived reported peers: {len(reported_peers)}")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # //  Persisted peers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _remove_persisted_peer(self, persisted_peer: "Peer") -> bool:
        if persisted_peer in self.get_persisted_peers():
            self.get_persisted_peers().discard(persisted_peer)
            self._request_persistence()
            return True
        return False

    def _request_persistence(self):
        self._persistence_manager.request_persistence()

    def _remove_persisted_peer_address(self, node_address: "NodeAddress") -> bool:
        peer = self._find_persisted_peer(node_address)
        if peer:
            return self._remove_persisted_peer(peer)
        return False

    def _find_persisted_peer(self, node_address: "NodeAddress") -> Optional["Peer"]:
        return next(
            (
                peer
                for peer in self.get_persisted_peers()
                if peer.node_address == node_address
            ),
            None,
        )

    def _remove_too_old_persisted_peers(self):
        old_peers = {
            reported_peer
            for reported_peer in self.get_persisted_peers()
            if get_time_ms() - reported_peer.date > PeerManager.MAX_AGE
        }
        for peer in old_peers:
            self._remove_persisted_peer(peer)

    def _purge_persisted_peers_if_exceeds(self):
        size = len(self.get_persisted_peers())
        if size > PeerManager.MAX_PERSISTED_PEERS:
            self.logger.trace(
                f"We have already {size} persisted peers which exceeds our limit of {PeerManager.MAX_PERSISTED_PEERS}."
                + "We remove random peers from the persisted peers list."
            )
            # we don't use sorting by lastActivityDate to avoid attack vectors and keep it more random
            peers_to_remove = random.sample(
                list(self.get_persisted_peers()), size - PeerManager.MAX_PERSISTED_PEERS
            )
            for peer in peers_to_remove:
                self._remove_persisted_peer(peer)
        else:
            self.logger.trace(
                f"No need to purge persisted peers.\n\tWe don't have more then {PeerManager.MAX_PERSISTED_PEERS} persisted peers yet."
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_max_connections(self) -> int:
        return self._max_connections

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listener(self, listener: "Listener"):
        self._listeners.add(listener)

    def remove_listener(self, listener: "Listener"):
        self._listeners.discard(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # //  Private misc
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_connected_reported_peers(self) -> set["Peer"]:
        result = set["Peer"]()

        # networkNode.getConfirmedConnections includes connections where peers_node_address is present
        for connection in self._network_node.get_confirmed_connections():
            supported_capabilities = Capabilities(connection.capabilities)
            # If we have a new connection the supported_capabilities is empty.
            # We lookup if we have already stored the supported_capabilities at the persisted or reported peers
            # and if so we use that.
            peers_node_address = connection.peers_node_address
            check_argument(
                peers_node_address,
                "connection missing node address at _get_connected_reported_peers",
            )  # confirmed connections should always have node address

            capabilities_not_found_in_connection = supported_capabilities.is_empty()
            if capabilities_not_found_in_connection:
                # If not found in connection we look up if we got the Capabilities set from any of the
                # reported or persisted peers
                persisted_and_reported = self.get_persisted_peers().copy()
                persisted_and_reported.update(self.get_reported_peers())

                candidate = next(
                    (
                        peer
                        for peer in persisted_and_reported
                        if peer.node_address == peers_node_address
                        and not peer.capabilities.is_empty()
                    ),
                    None,
                )

                if candidate:
                    supported_capabilities = candidate.capabilities

            peer = Peer(
                node_address=peers_node_address, capabilities=supported_capabilities
            )

            # If we did not find the capability from our own connection we add a listener,
            # so once we get a connection with that peer and exchange a message containing the capabilities
            # we get set the capabilities.
            if capabilities_not_found_in_connection:
                connection.add_weak_capabilities_listener(peer)

            result.add(peer)

        return result

    def _stop_check_max_connections_timer(self):
        if self._check_max_connections_timer:
            self._check_max_connections_timer.stop()
            self._check_max_connections_timer = None

    def _print_statistics(self):
        result = f"Connection statistics:\n"
        # Sort connections by creation timestamp
        sorted_connections = sorted(
            self._network_node.get_all_connections(),
            key=lambda conn: conn.connection_statistics.connection_creation_timestamp,
        )

        # Build the stats string
        for i, conn in enumerate(sorted_connections, 1):
            result += f"\nConnection {i}\n" f"{conn.connection_statistics.get_info()}\n"

        self.logger.info(result)

    def _print_connected_peers(self):
        confirmed = self._network_node.get_confirmed_connections()
        if confirmed:
            result = (
                "\n\n------------------------------------------------------------\n"
                f"Connected peers for node {self._network_node.node_address_property.value}:"
            )

            for connection in confirmed:
                result += f"\n{connection.peers_node_address} {connection.connection_state.peer_type.name}"

            result += "\n------------------------------------------------------------\n"
            self.logger.debug(result)
