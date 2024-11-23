from abc import ABC, abstractmethod
from datetime import timedelta
import random
from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.peers.getdata.get_data_request_handler import (
    GetDataRequestHandler,
)
from bisq.core.network.p2p.peers.getdata.request_data_handler import RequestDataHandler
from bisq.core.network.p2p.peers.getdata.messages.get_data_request import GetDataRequest
from bisq.core.network.p2p.peers.peerexchange.peer import Peer
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
import bisq.common.version as Version
from utils.concurrency import ThreadSafeList
from utils.data import SimplePropertyChangeEvent
from bisq.core.network.p2p.peers.peer_manager import PeerManager

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage

logger = get_logger(__name__)


class RequestDataManager(MessageListener, ConnectionListener, PeerManager.Listener):
    RETRY_DELAY_SEC = 10
    CLEANUP_TIMER = 120
    # How many seeds we request the PreliminaryGetDataRequest from
    NUM_SEEDS_FOR_PRELIMINARY_REQUEST = 2
    # How many seeds additional to the first responding PreliminaryGetDataRequest seed we request the GetUpdatedDataRequest from
    NUM_ADDITIONAL_SEEDS_FOR_UPDATE_REQUEST = 1
    MAX_REPEATED_REQUESTS = 30

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    class Listener(ABC):
        @abstractmethod
        def on_preliminary_data_received(self):
            pass

        @abstractmethod
        def on_updated_data_received(self):
            pass

        @abstractmethod
        def on_data_received(self):
            pass

        def on_no_peers_available(self):
            pass

        def on_no_seed_node_available(self):
            pass

    class ResponseListener:
        @abstractmethod
        def on_success(self, serialized_size: int):
            pass

        @abstractmethod
        def on_fault(self):
            pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Class fields
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def __init__(
        self,
        network_node: "NetworkNode",
        seed_node_repository: "SeedNodeRepository",
        data_storage: "P2PDataStorage",
        peer_manager: "PeerManager",
    ):
        self.network_node = network_node
        self.data_storage = data_storage
        self.peer_manager = peer_manager
        self.seed_node_repository = seed_node_repository

        self.response_listeners: ThreadSafeList[
            "RequestDataManager.ResponseListener"
        ] = ThreadSafeList()

        self.is_preliminary_data_request = True

        # P2PService calls the setListener
        # in its constructor so we can guarantee it is not null.
        self.listener: "RequestDataManager.Listener" = None

        self.handler_map: dict["NodeAddress", "RequestDataHandler"] = {}
        self.get_data_request_handlers: dict[str, "GetDataRequestHandler"] = {}
        self.node_address_of_preliminary_data_request: Optional["NodeAddress"] = None
        self.retry_timer: Optional[Timer] = None
        self.data_update_requested = False
        self.all_data_received = False
        self.stopped = False
        self.num_repeated_requests = 0

        self.network_node.add_message_listener(self)
        self.network_node.add_connection_listener(self)
        self.peer_manager.add_listener(self)

        self.seed_node_addresses = list(seed_node_repository.get_seed_node_addresses())
        # We shuffle only once so that we use the same seed nodes for preliminary and updated data requests.
        random.shuffle(self.seed_node_addresses)

        self.network_node.node_address_property.add_listener(self._on_node_address_changed)

    def _on_node_address_changed(self, e: "SimplePropertyChangeEvent"):
        if e.new_value is not None:
            if e.new_value in self.seed_node_addresses:
                self.seed_node_addresses.remove(e.new_value)
            if self.seed_node_repository.is_seed_node(e.new_value):
                RequestDataManager.NUM_SEEDS_FOR_PRELIMINARY_REQUEST = 3
                RequestDataManager.NUM_ADDITIONAL_SEEDS_FOR_UPDATE_REQUEST = 2
                RequestDataManager.MAX_REPEATED_REQUESTS = 100

    def shut_down(self):
        self.stopped = True
        self.stop_retry_timer()
        self.network_node.remove_message_listener(self)
        self.network_node.remove_connection_listener(self)
        self.peer_manager.remove_listener(self)
        self.close_all_handlers()

    # /////////////////////////////////////////////////////////////////////////////////////////
    # API
    # /////////////////////////////////////////////////////////////////////////////////////////

    # We only support one listener as P2PService will manage calls on other clients in the correct order of execution.
    # The listener is set from the P2PService constructor so we can guarantee it is not null.
    def set_listener(self, listener: "RequestDataManager.Listener"):
        self.listener = listener

    def request_preliminary_data(self):
        node_addresses = list(self.seed_node_addresses)
        if node_addresses:
            final_node_addresses = list(node_addresses)
            size = min(
                RequestDataManager.NUM_SEEDS_FOR_PRELIMINARY_REQUEST, len(final_node_addresses)
            )
            for i in range(size):
                node_address = final_node_addresses[i]
                node_addresses.remove(node_address)
                # We clone list to avoid mutable change during iterations
                remaining_node_addresses = list(node_addresses)
                UserThread.run_after(
                    lambda: self.request_data(node_address, remaining_node_addresses),
                    timedelta(milliseconds=i * 200 + 1),
                )
            self.is_preliminary_data_request = True
        else:
            assert self.listener
            self.listener.on_no_seed_node_available()

    def request_update_data(self):
        assert (
            self.node_address_of_preliminary_data_request
        ), "node_address_of_preliminary_data_request must be present"
        self.data_update_requested = True
        self.is_preliminary_data_request = False
        node_addresses = list(self.seed_node_addresses)
        if node_addresses:
            # We use the node we have already connected to to request again
            candidate = self.node_address_of_preliminary_data_request
            if candidate:
                if candidate in node_addresses:
                    node_addresses.remove(candidate)
                self.request_data(candidate, node_addresses)

                final_node_addresses = list(node_addresses)
                num_requests = 0
                for i in range(len(final_node_addresses)):
                    if num_requests >= RequestDataManager.NUM_ADDITIONAL_SEEDS_FOR_UPDATE_REQUEST:
                        break
                    node_address = final_node_addresses[i]
                    node_addresses.remove(node_address)

                    # It might be that we have a prelim. request open for the same seed, if so we skip to the next.
                    if node_address not in self.handler_map:
                        UserThread.run_after(
                            lambda: self.request_data(node_address, node_addresses),
                            timedelta(milliseconds=i * 200 + 1),
                        )
                        num_requests += 1

    def get_node_address_of_preliminary_data_request(self) -> Optional[NodeAddress]:
        return self.node_address_of_preliminary_data_request

    def add_response_listener(
        self, response_listener: "RequestDataManager.ResponseListener"
    ):
        self.response_listeners.append(response_listener)

    # /////////////////////////////////////////////////////////////////////////////////////////
    # ConnectionListener implementation
    # /////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection: "Connection"):
        pass

    def on_disconnect(
        self, close_connection_reason: "CloseConnectionReason", connection: "Connection"
    ):
        self.close_handler(connection)

        if (
            self.peer_manager.is_peer_banned(close_connection_reason, connection)
            and connection.peers_node_address
        ):
            node_address = connection.peers_node_address
            if node_address in self.seed_node_addresses:
                self.seed_node_addresses.remove(node_address)
            self.handler_map.pop(node_address, None)

    # /////////////////////////////////////////////////////////////////////////////////////////
    # PeerManager.Listener implementation
    # /////////////////////////////////////////////////////////////////////////////////////////

    def on_all_connections_lost(self):
        self.close_all_handlers()
        self.stop_retry_timer()
        self.stopped = True
        self.restart()

    def on_new_connection_after_all_connections_lost(self):
        self.close_all_handlers()
        self.stopped = False
        self.restart()

    def on_awake_from_standby(self):
        self.close_all_handlers()
        self.stopped = False
        if self.network_node.get_all_connections():
            self.restart()

    # /////////////////////////////////////////////////////////////////////////////////////////
    # MessageListener implementation
    # /////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, GetDataRequest):
            if not self.stopped:
                get_data_request = network_envelope
                if get_data_request.version is None or not Version.is_new_version(
                    get_data_request.version, "1.5.0"
                ):
                    connection.shut_down(
                        CloseConnectionReason.MANDATORY_CAPABILITIES_NOT_SUPPORTED
                    )
                    return
                uid = connection.uid
                if uid not in self.get_data_request_handlers:
                    class Listener(GetDataRequestHandler.Listener):
                        
                        def __init__(self, request_data_manager: "RequestDataManager") -> None:
                            super().__init__()
                            self.request_data_manager = request_data_manager
                        
                        def on_complete(self, serialized_size: int):
                            self.request_data_manager._on_get_data_request_complete(
                                uid, serialized_size, connection
                            )

                        def on_fault(self, error_message: str, conn: "Connection"):
                            self.request_data_manager._on_get_data_request_fault(uid, error_message, conn)
                            
                    listener = Listener(self)
                    get_data_request_handler = GetDataRequestHandler(
                        self.network_node, self.data_storage, listener
                    )
                    self.get_data_request_handlers[uid] = get_data_request_handler
                    get_data_request_handler.handle(get_data_request, connection)
                else:
                    logger.warning(
                        "We have already a GetDataRequestHandler for that connection started. "
                        "We start a cleanup timer if the handler has not closed by itself in between 2 minutes."
                    )
                    UserThread.run_after(
                        lambda: self._cleanup_get_data_request_handler(uid),
                        timedelta(seconds=self.CLEANUP_TIMER),
                    )
            else:
                logger.warning(
                    "We have stopped already. We ignore that on_message call."
                )

    def _on_get_data_request_complete(self, uid: str, serialized_size: int, connection: "Connection"):
        self.get_data_request_handlers.pop(uid, None)
        logger.trace(f"requestDataHandshake completed.\n\tConnection={connection}")
        for listener in self.response_listeners:
            listener.on_success(serialized_size)

    def _on_get_data_request_fault(self, uid: str, error_message: str, connection: "Connection"):
        self.get_data_request_handlers.pop(uid, None)
        if not self.stopped:
            logger.trace(
                f"GetDataRequestHandler failed.\n\tConnection={connection}\n\tErrorMessage={error_message}"
            )
            self.peer_manager.handle_connection_fault(connection=connection)
            for listener in self.response_listeners:
                listener.on_fault()
        else:
            logger.warning(
                "We have stopped already. We ignore that getDataRequestHandler.handle.onFault call."
            )

    def _cleanup_get_data_request_handler(self, uid):
        if uid in self.get_data_request_handlers:
            handler = self.get_data_request_handlers[uid]
            handler.stop()
            del self.get_data_request_handlers[uid]

    # /////////////////////////////////////////////////////////////////////////////////////////
    # RequestData
    # /////////////////////////////////////////////////////////////////////////////////////////

    def request_data(
        self, node_address: "NodeAddress", remaining_node_addresses: list["NodeAddress"]
    ):
        if not self.stopped:
            if node_address not in self.handler_map:
                class Listener(RequestDataHandler.Listener):
                    def __init__(
                        self,
                        request_data_manager: "RequestDataManager",
                    ):
                        super().__init__()
                        self.request_data_manager = request_data_manager
                        
                    def on_complete(self, was_truncated: bool):
                        self.request_data_manager._on_request_data_complete(
                            node_address, was_truncated, remaining_node_addresses
                        ),
                    
                    def on_fault(self, error_message: str, conn: "Connection"):
                        self.request_data_manager._on_request_data_fault(
                            node_address, error_message, conn, remaining_node_addresses
                        )

                listener = Listener(self)
                request_data_handler = RequestDataHandler(
                    self.network_node, self.data_storage, self.peer_manager, listener
                )
                self.handler_map[node_address] = request_data_handler
                self.num_repeated_requests += 1
                request_data_handler.request_data(
                    node_address, self.is_preliminary_data_request
                )
            else:
                logger.warning(
                    f"We have started already a requestDataHandshake to peer. nodeAddress={node_address}\n"
                    f"We start a cleanup timer if the handler has not closed by itself in between 2 minutes."
                )
                UserThread.run_after(
                    lambda: self._cleanup_request_data_handler(node_address),
                    timedelta(seconds=self.CLEANUP_TIMER),
                )
        else:
            logger.warning("We have stopped already. We ignore that request_data call.")

    def _on_request_data_complete(
        self,
        node_address: "NodeAddress",
        was_truncated: bool,
        remaining_node_addresses: list["NodeAddress"],
    ):
        logger.trace(
            f"RequestDataHandshake of outbound connection complete. nodeAddress={node_address}"
        )
        self.stop_retry_timer()
        
        # need to remove before listeners are notified as they cause the update call
        self.handler_map.pop(node_address, None)
        
        # 1. We get a response from requestPreliminaryData
        if not self.node_address_of_preliminary_data_request:
            self.node_address_of_preliminary_data_request = node_address
            # We delay because it can be that we get the HS published before we receive the
            # preliminary data and the onPreliminaryDataReceived call triggers the
            # dataUpdateRequested set to true, so we would also call the onUpdatedDataReceived.
            assert self.listener
            UserThread.run_after(self.listener.on_preliminary_data_received, timedelta(milliseconds=100))
        
        # 2. Later we get a response from requestUpdatesData
        if self.data_update_requested:
            self.data_update_requested = False
            assert self.listener
            self.listener.on_updated_data_received()
                
        
        if was_truncated:
            if self.num_repeated_requests < RequestDataManager.MAX_REPEATED_REQUESTS:
                # If we had allDataReceived already set to true but get a response with truncated flag,
                # we still repeat the request to that node for higher redundancy. Otherwise, one seed node
                # providing incomplete data would stop others to fill the gaps.
                logger.info(
                    "DataResponse did not contain all data, so we repeat request until we got all data"
                )
                UserThread.run_after(
                    lambda: self.request_data(node_address, remaining_node_addresses), timedelta(seconds=2)
                )
            elif not self.all_data_received:
                self.all_data_received = True
                logger.warning(
                    "\n#################################################################\n"
                    f"Loading initial data from {node_address} did not complete after 20 repeated requests.\n"
                    "#################################################################\n"
                )
                assert self.listener
                self.listener.on_data_received()
        elif not self.all_data_received:
            self.all_data_received = True
            logger.info(
                "\n\n#################################################################\n"
                f"Loading initial data from {node_address} completed\n"
                "#################################################################\n"
            )
            assert self.listener
            self.listener.on_data_received()

    def _on_request_data_fault(
        self,
        node_address: "NodeAddress",
        error_message: str,
        connection: Optional["Connection"],
        remaining_node_addresses: list["NodeAddress"],
    ):
        logger.trace(
            f"requestDataHandshake with outbound connection failed.\n\tnodeAddress={node_address}\n\t"
            f"ErrorMessage={error_message}"
        )
        self.peer_manager.handle_connection_fault(node_address=node_address)
        self.handler_map.pop(node_address, None)

        if remaining_node_addresses:
            logger.debug(
                "There are remaining nodes available for requesting data. "
                "We will try requestDataFromPeers again."
            )
            next_candidate = remaining_node_addresses.pop(0)
            self.request_data(next_candidate, remaining_node_addresses)
        elif not self.handler_map:
            # If not other connection attempts are in the handlerMap we assume that no seed
            # nodes are available.
            logger.debug(
                "There is no remaining node available for requesting data. "
                "That is expected if no other node is online.\n\t"
                "We will try to use reported peers (if no available we use persisted peers) "
                "and try again to request data from our seed nodes after a random pause."
            )
            
            # Notify listeners
            if not self.node_address_of_preliminary_data_request:
                if self.peer_manager.is_seed_node(node_address):
                    assert self.listener
                    self.listener.on_no_seed_node_available()
                else:
                    assert self.listener
                    self.listener.on_no_peers_available()
            self.request_from_non_seed_node_peers()
        else:
            logger.info(
                f"We could not connect to seed node {node_address.get_full_address()} but "
                 "we have other connection attempts open."
            )

    def _cleanup_request_data_handler(self, node_address: "NodeAddress"):
        if node_address in self.handler_map:
            handler = self.handler_map[node_address]
            handler.stop()
            del self.handler_map[node_address]

    # /////////////////////////////////////////////////////////////////////////////////////////
    # Utils
    # /////////////////////////////////////////////////////////////////////////////////////////

    def request_from_non_seed_node_peers(self):
        list_ = self.get_filtered_non_seed_node_list(
            self.get_sorted_node_addresses(self.peer_manager.get_reported_peers()), []
        )
        filtered_persisted_peers = self.get_filtered_non_seed_node_list(
            self.get_sorted_node_addresses(self.peer_manager.get_persisted_peers()),
            list_,
        )
        list_.extend(filtered_persisted_peers)

        if list_:
            next_candidate = list_.pop(0)
            self.request_data(next_candidate, list_)

    def restart(self):
        if self.retry_timer is None:

            def _restart():
                self.stopped = False
                self.stop_retry_timer()
                
                # We create a new list of candidates
                # 1. shuffled seedNodes
                # 2. reported peers sorted by last activity date
                # 3. Add as last persisted peers sorted by last activity date
                list_ = self.get_filtered_list(list(self.seed_node_addresses), [])
                random.shuffle(list_)

                filtered_reported_peers = self.get_filtered_non_seed_node_list(
                    self.get_sorted_node_addresses(
                        self.peer_manager.get_reported_peers()
                    ),
                    list_,
                )
                list_.extend(filtered_reported_peers)

                filtered_persisted_peers = self.get_filtered_non_seed_node_list(
                    self.get_sorted_node_addresses(
                        self.peer_manager.get_persisted_peers()
                    ),
                    list_,
                )
                list_.extend(filtered_persisted_peers)

                if list_:
                    next_candidate = list_.pop(0)
                    self.request_data(next_candidate, list_)

            self.retry_timer = UserThread.run_after(_restart, timedelta(seconds=RequestDataManager.RETRY_DELAY_SEC))

    def get_sorted_node_addresses(self, collection: list[Peer]) -> list["NodeAddress"]:
        return [
            peer.node_address
            for peer in sorted(collection, key=lambda p: p.get_date(), reverse=True)
        ]

    def get_filtered_list(
        self, collection: list["NodeAddress"], list_: list["NodeAddress"]
    ) -> list["NodeAddress"]:
        return [
            e for e in collection if e not in list_ and not self.peer_manager.is_self(e)
        ]

    def get_filtered_non_seed_node_list(
        self, collection: list["NodeAddress"], list_: list["NodeAddress"]
    ) -> list["NodeAddress"]:
        return [
            e
            for e in self.get_filtered_list(collection, list_)
            if not self.peer_manager.is_seed_node(e)
        ]

    def stop_retry_timer(self):
        if self.retry_timer is not None:
            self.retry_timer.stop()
            self.retry_timer = None

    def close_handler(self, connection: "Connection"):
        node_address = connection.peers_node_address
        if node_address:
            if node_address in self.handler_map:
                self.handler_map[node_address].cancel()
                del self.handler_map[node_address]
        else:
            logger.trace(
                f"closeRequestDataHandler: node_address not set in connection {connection}"
            )

    def close_all_handlers(self):
        for handler in self.handler_map.values():
            handler.cancel()
        self.handler_map.clear()
