from abc import ABC, abstractmethod
from concurrent.futures import Future
from datetime import timedelta
from typing import TYPE_CHECKING, Generic, Optional, TypeVar
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.message_listener import MessageListener
from utils.random import next_random_int

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.dao.monitoring.network.messages.get_state_hashes_request import (
        GetStateHashesRequest,
    )
    from bisq.core.dao.monitoring.network.messages.get_state_hashes_response import (
        GetStateHashesResponse,
    )
    from bisq.core.network.p2p.network.connection import Connection

logger = get_logger(__name__)


_Req = TypeVar("Req", bound="GetStateHashesRequest")
_Res = TypeVar("Res", bound="GetStateHashesResponse")


class RequestStateHashesHandler(Generic[_Req, _Res], MessageListener, ABC):
    TIMEOUT_SEC = 180

    class Listener(Generic[_Res], ABC):
        @abstractmethod
        def on_complete(
            self, get_state_hashes_response: _Res, peers_node_address: Optional["NodeAddress"]
        ) -> None:
            pass

        @abstractmethod
        def on_fault(self, error_message: str, connection: Optional["Connection"]) -> None:
            pass

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        node_address: "NodeAddress",
        listener: "RequestStateHashesHandler.Listener[_Res]",
    ):
        self._network_node = network_node
        self._peer_manager = peer_manager
        self._node_address = node_address
        self._listener = listener
        self._timeout_timer: Optional[Timer] = None
        self.nonce = next_random_int()
        self._stopped = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def get_get_state_hashes_request(self, from_height: int) -> _Req:
        pass

    @abstractmethod
    def cast_to_get_state_hashes_response(
        self, network_envelope: "NetworkEnvelope"
    ) -> _Res:
        pass

    @abstractmethod
    def is_get_state_hashes_response(self, network_envelope: "NetworkEnvelope") -> bool:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_state_hashes(self, from_height: int) -> None:
        if not self._stopped:
            get_state_hashes_request = self.get_get_state_hashes_request(from_height)
            if self._timeout_timer is None:
                self._timeout_timer = UserThread.run_after(
                    lambda: self._handle_timeout(get_state_hashes_request),
                    timedelta(seconds=RequestStateHashesHandler.TIMEOUT_SEC),
                )

            logger.debug(
                f"We send to peer {self._node_address} a {get_state_hashes_request}."
            )
            self._network_node.add_message_listener(self)
            future = self._network_node.send_message(
                self._node_address, get_state_hashes_request
            )
            future.add_done_callback(
                self._handle_send_message_result(get_state_hashes_request)
            )
        else:
            logger.warning(
                "We have stopped already. We ignore that requestProposalsHash call."
            )

    def _handle_timeout(self, get_state_hashes_request: _Req) -> None:
        if not self._stopped:
            error_message = (
                f"A timeout occurred at sending getStateHashesRequest: {get_state_hashes_request} "
                f"on peersNodeAddress: {self._node_address}"
            )
            logger.debug(f"{error_message} / RequestStateHashesHandler={self}")
            self._handle_fault(error_message, self._node_address, "SEND_MSG_TIMEOUT")
        else:
            logger.trace(
                "We have stopped already. We ignore that timeout_timer.run call. "
                "Might be caused by a previous network_node.send_message.on_failure."
            )

    def _handle_send_message_result(self, get_state_hashes_request: _Req):
        def callback(future: Future):
            try:
                future.result()
                if not self._stopped:
                    logger.info(
                        f"Sending of {get_state_hashes_request.__class__.__name__} message to peer {self._node_address.get_full_address()} succeeded."
                    )
                else:
                    logger.trace(
                        "We have stopped already. We ignore that network_node.send_message.on_success call. "
                        "Might be caused by a previous timeout."
                    )
            except Exception as e:
                if not self._stopped:
                    error_message = (
                        f"Sending getStateHashesRequest to {self._node_address} failed. "
                        f"That is expected if the peer is offline.\n\tgetStateHashesRequest={get_state_hashes_request}."
                        f"\n\tException={e}"
                    )
                    logger.error(error_message)
                    self._handle_fault(
                        error_message,
                        self._node_address,
                        CloseConnectionReason.SEND_MSG_FAILURE,
                    )
                else:
                    logger.trace(
                        "We have stopped already. We ignore that network_node.send_message.on_failure call. "
                        "Might be caused by a previous timeout."
                    )

        return callback

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(
        self, network_envelope: "NetworkEnvelope", connection: "Connection"
    ) -> None:
        if self.is_get_state_hashes_response(network_envelope):
            if (
                connection.peers_node_address
                and connection.peers_node_address == self._node_address
            ):
                if not self._stopped:
                    get_state_hashes_response = self.cast_to_get_state_hashes_response(
                        network_envelope
                    )
                    if get_state_hashes_response.request_nonce == self.nonce:
                        self._stop_timeout_timer()
                        self._cleanup()
                        logger.info(
                            f"We received from peer {self._node_address.get_full_address()} a {get_state_hashes_response.__class__.__name__} with {len(get_state_hashes_response.state_hashes)} stateHashes"
                        )
                        self._listener.on_complete(
                            get_state_hashes_response,
                            connection.peers_node_address,
                        )
                    else:
                        logger.warning(
                            f"Nonce not matching. That can happen rarely if we get a response after a canceled "
                            f"handshake (timeout causes connection close but peer might have sent a msg before "
                            f"connection was closed).\n\t"
                            f"We drop that message. nonce={self.nonce} / requestNonce={get_state_hashes_response.request_nonce}"
                        )
                else:
                    logger.warning("We have stopped already.")
            elif connection.peers_node_address:
                logger.debug(
                    f"{self.__class__.__name__}: We got a message from another node. We ignore that."
                )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _handle_fault(
        self,
        error_message: str,
        node_address: "NodeAddress",
        reason: "CloseConnectionReason",
    ) -> None:
        self._cleanup()
        self._peer_manager.handle_connection_fault(node_address=node_address)
        self._listener.on_fault(error_message, None)

    def _cleanup(self) -> None:
        self._stopped = True
        self._network_node.remove_message_listener(self)
        self._stop_timeout_timer()

    def _stop_timeout_timer(self) -> None:
        if self._timeout_timer is not None:
            self._timeout_timer.stop()
            self._timeout_timer = None
