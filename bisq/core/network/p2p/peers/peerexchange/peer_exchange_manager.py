from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.peers.peer_manager import PeerManager
from bisq.core.network.p2p.peers.peerexchange.get_peers_request_handler import GetPeersRequestHandler
from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_request import GetPeersRequest
from bisq.core.network.p2p.peers.peerexchange.peer_exchange_handler import PeerExchangeHandler
import random

if TYPE_CHECKING:
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.peers.peerexchange.peer import Peer
    from bisq.core.network.p2p.network.network_node import NetworkNode

logger = get_logger(__name__)


class PeerExchangeManager(MessageListener, ConnectionListener, PeerManager.Listener):
    RETRY_DELAY_SEC = 10
    RETRY_DELAY_AFTER_ALL_CON_LOST_SEC = 3
    REQUEST_PERIODICALLY_INTERVAL_MIN = 10

    def __init__(self, network_node: "NetworkNode",
                 seed_node_repository: "SeedNodeRepository",
                 peer_manager: "PeerManager"):
        self.handler_map: dict["NodeAddress", "PeerExchangeHandler"] = {}
        
        self.retry_timer: Optional["Timer"] = None
        self.periodic_timer: Optional["Timer"] = None
        self.stopped = False
        
        self.network_node = network_node
        self.peer_manager = peer_manager
        
        self.network_node.add_message_listener(self)
        self.network_node.add_connection_listener(self)
        self.peer_manager.add_listener(self)
        
        self.seed_node_addresses: set["NodeAddress"] = set(seed_node_repository.get_seed_node_addresses())

    def shut_down(self):
        self.stopped = True
        self.network_node.remove_message_listener(self)
        self.network_node.remove_connection_listener(self)
        self.peer_manager.remove_listener(self)

        self._stop_periodic_timer()
        self._stop_retry_timer()
        self._close_all_handlers()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_reported_peers_from_seed_nodes(self, node_address: "NodeAddress"):
        assert self.network_node.node_address_property.value, "My node address must not be null at request_reported_peers"
        remaining_node_addresses = list(self.seed_node_addresses)
        if node_address in remaining_node_addresses:
            remaining_node_addresses.remove(node_address)
        random.shuffle(remaining_node_addresses)
        self.request_reported_peers(node_address, remaining_node_addresses)
        
        self._start_periodic_timer()

    def initial_request_peers_from_reported_or_persisted_peers(self):
        if self.peer_manager.get_reported_peers() or self.peer_manager.get_persisted_peers():
            # We will likely get more connections as the GetPeersResponse onComplete handler triggers a new request if the confirmed
            # connections have not reached the min connection target.
            # So we potentially request 2 times 8 but we prefer to get fast connected
            # and disconnect afterwards when we exceed max connections rather to delay connection in case many of our peers from the list are dead.
            for _ in range(min(8, self.peer_manager.get_max_connections())):
                self.request_with_available_peers()
        else:
            logger.info("We don't have any reported or persisted peers, so we need to wait until we receive from the seed node the initial peer list.")


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection):
        pass

    def on_disconnect(self, close_connection_reason, connection):
        logger.debug(f"onDisconnect closeConnectionReason={close_connection_reason}, nodeAddressOpt={connection.peers_node_address}")
        self._close_handler(connection)

        if self.retry_timer is None:
            def retry_action():
                logger.trace("ConnectToMorePeersTimer called from onDisconnect code path")
                self._stop_retry_timer()
                self.request_with_available_peers()

            self.retry_timer = UserThread.run_after(retry_action, timedelta(seconds=PeerExchangeManager.RETRY_DELAY_SEC))

        if self.peer_manager.is_peer_banned(close_connection_reason, connection):
            node_address = connection.peers_node_address
            if node_address:
                self.seed_node_addresses.discard(node_address)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PeerManager.Listener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_connections_lost(self):
        self._close_all_handlers()
        self._stop_periodic_timer()
        self._stop_retry_timer()
        self.stopped = True
        self._restart()

    def on_new_connection_after_all_connections_lost(self):
        self._close_all_handlers()
        self.stopped = False
        self._restart()

    def on_awake_from_standby(self):
        self._close_all_handlers()
        self.stopped = False
        if self.network_node.get_all_connections():
            self._restart()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def on_message(self, network_envelope, connection):
        if isinstance(network_envelope, GetPeersRequest):
            if self.stopped:
                logger.warning("We have stopped already. We ignore that onMessage call.")
                return 

            class Listener(GetPeersRequestHandler.Listener):
                def __init__(self, peer_manager: "PeerManager"):
                    self.peer_manager = peer_manager
                
                def on_complete(self):
                    logger.trace(f"PeerExchangeHandshake completed.\nConnection={connection}")

                def on_fault(self, error_message, connection):
                    logger.trace(f"PeerExchangeHandshake failed.\nerrorMessage={error_message}\n"
                                            f"connection={connection}")
                    self.peer_manager.handle_connection_fault(connection=connection)

            get_peers_request_handler = GetPeersRequestHandler(
                self.network_node,
                self.peer_manager,
                Listener(self.peer_manager)
            )
            get_peers_request_handler.handle(network_envelope, connection)
            
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Request
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_reported_peers(self, node_address: "NodeAddress", remaining_node_addresses: list["NodeAddress"]):
        logger.debug(f"requestReportedPeers nodeAddress={node_address}; remainingNodeAddresses.size={len(remaining_node_addresses)}")
        
        if self.stopped:
            logger.trace("We have stopped already. We ignore that requestReportedPeers call.")
            return
        
        if node_address not in self.handler_map:
            class Listener(PeerExchangeHandler.Listener):
                def __init__(self, outer: "PeerExchangeManager", node_address: "NodeAddress", remaining_node_addresses: list["NodeAddress"]):
                    self.outer = outer
                    self.node_address = node_address
                    self.remaining_node_addresses = remaining_node_addresses

                def on_complete(self):
                    self.outer.handler_map.pop(self.node_address)
                    self.outer.request_with_available_peers()

                def on_fault(self, error_message: str, connection: Optional["Connection"]):
                    logger.debug(f"PeerExchangeHandshake of outbound connection failed.\n\terrorMessage={error_message}\n\t"
                                f"nodeAddress={self.node_address}")

                    self.outer.peer_manager.handle_connection_fault(node_address=self.node_address)
                    self.outer.handler_map.pop(self.node_address)
                    
                    if self.remaining_node_addresses:
                        if not self.outer.peer_manager.has_sufficient_connections():
                            logger.debug("There are remaining nodes available for requesting peers. "
                                         "We will try getReportedPeers again.")
                            next_candidate = random.choice(self.remaining_node_addresses)
                            self.remaining_node_addresses.remove(next_candidate)
                            self.outer.request_reported_peers(next_candidate, self.remaining_node_addresses)
                        else:
                            # That path will rarely be reached
                            logger.debug("We have already sufficient connections.")
                    else:
                        logger.debug("There is no remaining node available for requesting peers. "
                                    "That is expected if no other node is online.\n\t"
                                    "We will try again after a pause.")
                        if self.outer.retry_timer is None:
                            def retry_action():
                                if not self.outer.stopped:
                                    logger.trace("retryTimer called from requestReportedPeers code path")
                                    self.outer._stop_retry_timer()
                                    self.outer.request_with_available_peers()
                                else:
                                    self.outer._stop_retry_timer()
                                    logger.warning("We have stopped already. We ignore that retryTimer.run call.")

                            self.outer.retry_timer = UserThread.run_after(retry_action, timedelta(seconds=PeerExchangeManager.RETRY_DELAY_SEC))

            peer_exchange_handler = PeerExchangeHandler(
                self.network_node,
                self.peer_manager,
                Listener(self, node_address, remaining_node_addresses)
            )
            self.handler_map[node_address] = peer_exchange_handler
            peer_exchange_handler.send_get_peers_request_after_random_delay(node_address)
        else:
            logger.trace(f"We have started already a peerExchangeHandler. "
                        f"We ignore that call. nodeAddress={node_address}")


    def request_with_available_peers(self):
        if self.stopped:
            logger.trace("We have stopped already. We ignore that request_with_available_peers call.")
            return
        
        if self.peer_manager.has_sufficient_connections():
            logger.debug("We have already sufficient connections.")
            return
        
        # We create a new list of not connected candidates
        # 1. shuffled reported peers
        # 2. shuffled persisted peers
        # 3. Add as last shuffled seedNodes (least priority)
        node_list = self._get_filtered_non_seed_node_list(
            self._get_node_addresses(self.peer_manager.get_reported_peers()), 
            []
        )
        random.shuffle(node_list)

        filtered_persisted_peers = self._get_filtered_non_seed_node_list(
            self._get_node_addresses(self.peer_manager.get_persisted_peers()), 
            node_list
        )
        random.shuffle(filtered_persisted_peers)
        node_list.extend(filtered_persisted_peers)

        filtered_seed_node_addresses = self._get_filtered_list(
            list(self.seed_node_addresses), 
            node_list
        )
        random.shuffle(filtered_seed_node_addresses)
        node_list.extend(filtered_seed_node_addresses)

        logger.debug(f"Number of peers in list for connect_to_more_peers: {len(node_list)}")
        logger.trace(f"Filtered connect_to_more_peers list: list={node_list}")
        
        if node_list:
            # Don't shuffle as we want the seed nodes at the last entries
            next_candidate = node_list[0]
            node_list.remove(next_candidate)
            self.request_reported_peers(next_candidate, node_list)
        else:
            logger.debug("No more peers are available for request_reported_peers. We will try again after a pause.")
            if self.retry_timer is None:
                def retry_action():
                    if not self.stopped:
                        logger.trace("retryTimer called from request_with_available_peers code path")
                        self._stop_retry_timer()
                        self.request_with_available_peers()
                    else:
                        self._stop_retry_timer()
                        logger.warning("We have stopped already. We ignore that retryTimer.run call.")

                self.retry_timer = UserThread.run_after(retry_action, timedelta(seconds=PeerExchangeManager.RETRY_DELAY_SEC))
            


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _start_periodic_timer(self):
        self.stopped = False
        if self.periodic_timer is None:
            self.periodic_timer = UserThread.run_periodically(
                self.request_with_available_peers,
                timedelta(minutes=PeerExchangeManager.REQUEST_PERIODICALLY_INTERVAL_MIN)
            )

    def _restart(self):
        self._start_periodic_timer()
        
        if self.retry_timer is not None:
            logger.debug("retryTimer already started")
            return
        
        def retry_action():
            self.stopped = False
            logger.trace("retryTimer called from restart")
            self._stop_retry_timer()
            self.request_with_available_peers()

        self.retry_timer = UserThread.run_after(
            retry_action,
            timedelta(seconds=PeerExchangeManager.RETRY_DELAY_AFTER_ALL_CON_LOST_SEC)
        )
            

    def _get_node_addresses(self, collection: list["Peer"]) -> list["NodeAddress"]:
        return [peer.node_address for peer in collection]

    def _get_filtered_list(self, collection: list["NodeAddress"], filter_list: list["NodeAddress"]) -> list["NodeAddress"]:
        return [
            addr for addr in collection
            if addr not in filter_list
            and not self.peer_manager.is_self(addr)
            and not self.peer_manager.is_confirmed(addr)
        ]

    def _get_filtered_non_seed_node_list(self, collection: list["NodeAddress"], filter_list: list["NodeAddress"]) -> list["NodeAddress"]:
        filtered = self._get_filtered_list(collection, filter_list)
        return [addr for addr in filtered if not self.peer_manager.is_seed_node(addr)]

    def _stop_periodic_timer(self):
        self.stopped = True
        if self.periodic_timer is not None:
            self.periodic_timer.stop()
            self.periodic_timer = None

    def _stop_retry_timer(self):
        if self.retry_timer is not None:
            self.retry_timer.stop()
            self.retry_timer = None

    def _close_handler(self, connection: "Connection"):
        peers_node_address = connection.peers_node_address
        if peers_node_address and peers_node_address in self.handler_map:
            self.handler_map[peers_node_address].cancel()
            del self.handler_map[peers_node_address]

    def _close_all_handlers(self):
        for handler in self.handler_map.values():
            handler.cancel()
        self.handler_map.clear()
