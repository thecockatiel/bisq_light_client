from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.message_listener import MessageListener
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.peers.broadcaster import Broadcaster
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.dao.monitoring.model.state_hash import StateHash
    from bisq.core.dao.monitoring.network.messages.get_state_hashes_request import (
        GetStateHashesRequest,
    )
    from bisq.core.dao.monitoring.network.messages.get_state_hashes_response import (
        GetStateHashesResponse,
    )
    from bisq.core.dao.monitoring.network.messages.new_state_hash_message import (
        NewStateHashMessage,
    )
    from bisq.core.dao.monitoring.network.request_state_hashes_handler import (
        RequestStateHashesHandler,
    )
    from bisq.core.network.p2p.network.connection import Connection


logger = get_logger(__name__)

_Msg = TypeVar("Msg", bound="NewStateHashMessage")
_Req = TypeVar("Req", bound="GetStateHashesRequest")
_Res = TypeVar("Res", bound="GetStateHashesResponse")
_Han = TypeVar("Han", bound="RequestStateHashesHandler")
_StH = TypeVar("StH", bound="StateHash")


class StateNetworkService(Generic[_Msg, _Req, _Res, _Han, _StH], MessageListener, ABC):

    class Listener(Generic[_Msg, _Req, _StH], ABC):

        @abstractmethod
        def on_new_state_hash_message(
            self, new_state_hash_message: _Msg, connection: "Connection"
        ) -> None:
            pass

        @abstractmethod
        def on_get_state_hash_request(
            self, connection: "Connection", get_state_hash_request: _Req
        ) -> None:
            pass

        @abstractmethod
        def on_peers_state_hashes(
            self, state_hashes: list[_StH], peers_node_address: Optional["NodeAddress"]
        ) -> None:
            pass

    class ResponseListener(ABC):
        @abstractmethod
        def on_success(self, serialized_size: int) -> None:
            pass

        @abstractmethod
        def on_fault(self) -> None:
            pass

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        broadcaster: "Broadcaster",
    ):
        self._network_node = network_node
        self._peer_manager = peer_manager
        self._broadcaster = broadcaster
        self._request_state_hash_handler_map: dict["NodeAddress", _Han] = {}
        self._listeners = ThreadSafeSet[
            "StateNetworkService.Listener[_Msg, _Req, _StH]"
        ]()
        self._message_listener_added = False
        self._response_listeners = ThreadSafeSet[
            "StateNetworkService.ResponseListener"
        ]()

    @property
    def request_state_hash_handler_map(self):
        return self._request_state_hash_handler_map

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def cast_to_get_state_hash_request(
        self, network_envelope: "NetworkEnvelope"
    ) -> _Req:
        pass

    @abstractmethod
    def is_get_state_hashes_request(self, network_envelope: "NetworkEnvelope") -> bool:
        pass

    @abstractmethod
    def cast_to_new_state_hash_message(
        self, network_envelope: "NetworkEnvelope"
    ) -> _Msg:
        pass

    @abstractmethod
    def is_new_state_hash_message(self, network_envelope: "NetworkEnvelope") -> bool:
        pass

    @abstractmethod
    def get_get_state_hashes_response(
        self, nonce: int, state_hashes: list[_StH]
    ) -> _Res:
        pass

    @abstractmethod
    def get_new_state_hash_message(self, my_state_hash: _StH) -> _Msg:
        pass

    @abstractmethod
    def get_request_state_hashes_handler(
        self,
        node_address: "NodeAddress",
        listener: "RequestStateHashesHandler.Listener[_Res]",
    ) -> _Han:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(
        self, network_envelope: "NetworkEnvelope", connection: "Connection"
    ) -> None:
        if self.is_new_state_hash_message(network_envelope):
            new_state_hash_message = self.cast_to_new_state_hash_message(
                network_envelope
            )
            logger.debug(
                f"We received a {new_state_hash_message.__class__.__name__} from peer {connection.peers_node_address} with stateHash={new_state_hash_message.state_hash}"
            )
            for listener in self._listeners:
                listener.on_new_state_hash_message(new_state_hash_message, connection)
        elif self.is_get_state_hashes_request(network_envelope):
            get_state_hash_request = self.cast_to_get_state_hash_request(
                network_envelope
            )
            logger.debug(
                f"We received a {get_state_hash_request.__class__.__name__} from peer {connection.peers_node_address} for height={get_state_hash_request.height}"
            )
            for listener in self._listeners:
                listener.on_get_state_hash_request(connection, get_state_hash_request)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self) -> None:
        if not self._message_listener_added:
            self._network_node.add_message_listener(self)
            self._message_listener_added = True

    def send_get_state_hashes_response(
        self, connection: "Connection", nonce: int, state_hashes: list[_StH]
    ) -> None:
        get_state_hashes_response = self.get_get_state_hashes_response(
            nonce, state_hashes
        )
        logger.info(
            f"Send {get_state_hashes_response.__class__.__name__} with {len(state_hashes)} stateHashes to peer {connection.peers_node_address}"
        )
        future = self._network_node.send_message(connection, get_state_hashes_response)
        future.add_done_callback(
            lambda f: self._handle_send_get_state_hashes_response(
                f, get_state_hashes_response
            )
        )

    def _handle_send_get_state_hashes_response(
        self, future: "Future[Connection]", get_state_hashes_response: _Res
    ) -> None:
        try:
            future.result()

            def on_success():
                for listener in self._response_listeners:
                    listener.on_success(get_state_hashes_response.get_serialized_size())

            UserThread.execute(on_success)
        except Exception as e:

            def on_failure():
                for listener in self._response_listeners:
                    listener.on_fault()

            UserThread.execute(on_failure)

    def request_hashes_from_all_connected_seed_nodes(self, from_height: int) -> None:
        for connection in self._network_node.get_confirmed_connections():
            if self._peer_manager.is_seed_node(connection):
                peers_node_address = connection.peers_node_address
                if peers_node_address:
                    self.request_hashes_from_seed_node(from_height, peers_node_address)

    def broadcast_my_state_hash(self, my_state_hash: _StH) -> None:
        self._broadcaster.broadcast(
            self.get_new_state_hash_message(my_state_hash),
            self._network_node.node_address_property.get(),
        )

    def request_hashes(self, from_height: int, peers_address: str) -> None:
        self.request_hashes_from_seed_node(
            from_height, NodeAddress.from_full_address(peers_address)
        )

    def reset(self) -> None:
        self._request_state_hash_handler_map.clear()

    def add_response_listener(
        self, response_listener: "StateNetworkService.ResponseListener"
    ) -> None:
        self._response_listeners.add(response_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listener(
        self, listener: "StateNetworkService.Listener[_Msg, _Req, _StH]"
    ) -> None:
        self._listeners.add(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_hashes_from_seed_node(
        self, from_height: int, node_address: "NodeAddress"
    ) -> None:
        class Listener(RequestStateHashesHandler.Listener[_Res]):
            def on_complete(
                self_,
                get_state_hashes_response: _Res,
                peers_node_address: "Optional[NodeAddress]",
            ) -> None:
                self._request_state_hash_handler_map.pop(node_address, None)
                state_hashes = get_state_hashes_response.state_hashes
                for listener in self._listeners:
                    listener.on_peers_state_hashes(state_hashes, peers_node_address)

            def on_fault(
                self_, error_message: str, connection: "Optional[Connection]"
            ) -> None:
                logger.warning(
                    f"requestDaoStateHashesHandler with outbound connection failed.\n\tnodeAddress={node_address}\n\tErrorMessage={error_message}"
                )
                self._request_state_hash_handler_map.pop(node_address, None)

        request_state_hashes_handler = self.get_request_state_hashes_handler(
            node_address, Listener()
        )
        self._request_state_hash_handler_map[node_address] = (
            request_state_hashes_handler
        )
        request_state_hashes_handler.request_state_hashes(from_height)
