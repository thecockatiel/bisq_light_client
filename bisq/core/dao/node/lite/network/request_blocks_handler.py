from concurrent.futures import Future
from utils.aio import FutureCallback
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.dao.node.messages.get_blocks_request import GetBlocksRequest
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.common.user_thread import UserThread
from utils.random import next_random_int
from bisq.core.dao.node.messages.get_blocks_response import GetBlocksResponse

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.network.connection import Connection


class RequestBlocksHandler(MessageListener):
    """Sends a GetBlocksRequest to a full node and listens on corresponding GetBlocksResponse from the full node."""

    TIMEOUT_MIN = 4

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    class Listener:
        def on_complete(self_, get_blocks_response: "GetBlocksResponse"):
            pass

        def on_fault(
            self_, error_message: str, connection: Optional["Connection"] = None
        ):
            pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Constructor
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        node_address: "NodeAddress",
        start_block_height: int,
        listener: "RequestBlocksHandler.Listener",
    ):
        self.logger = get_ctx_logger(__name__)
        self._network_node = network_node
        self._peer_manager = peer_manager
        self.node_address = node_address
        self.start_block_height = start_block_height
        self._listener = listener
        self._timeout_timer: Optional["Timer"] = None
        self._future: Optional[Future] = None
        self._nonce = next_random_int()
        self._stopped = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_blocks(self):
        if self._stopped:
            self.logger.warning(
                "We have stopped already. We ignore that requestData call."
            )
            return

        get_blocks_request = GetBlocksRequest(
            self.start_block_height,
            self._nonce,
            self._network_node.node_address_property.get(),
        )

        if self._timeout_timer is not None:
            self.logger.warning("We had a timer already running and stop it.")
            self._timeout_timer.stop()

        def handle_timeout():
            if not self._stopped:
                error_message = (
                    f"A timeout occurred when sending getBlocksRequest: {get_blocks_request} "
                    f"on peersNodeAddress: {self.node_address}"
                )
                self.logger.debug(f"{error_message} / RequestDataHandler={self}")
                self._handle_fault(
                    error_message,
                    self.node_address,
                    CloseConnectionReason.SEND_MSG_TIMEOUT,
                )
            else:
                self.logger.warning(
                    "We have stopped already. We ignore that timeoutTimer.run call. "
                    "Might be caused by a previous networkNode.sendMessage.onFailure."
                )

        # setup before sending to avoid race conditions (?)
        self._timeout_timer = UserThread.run_after(
            handle_timeout,
            timedelta(minutes=RequestBlocksHandler.TIMEOUT_MIN),
        )

        self.logger.info(
            f"\n\n>> We request blocks from peer {self.node_address.get_full_address()} from block height {get_blocks_request.from_block_height}.\n"
        )

        self._network_node.add_message_listener(self)

        self._future = self._network_node.send_message(
            self.node_address, get_blocks_request
        )

        def on_success(result):
            self._future = None
            self.logger.debug(
                f"Sending of GetBlocksRequest message to peer {self.node_address.get_full_address()} succeeded."
            )

        def on_failure(e: Exception):
            self._future = None
            if not self._stopped:
                error_message = (
                    f"Sending getBlocksRequest to {self.node_address} failed. That is expected if the peer is offline.\n\t"
                    f"getBlocksRequest={get_blocks_request}.\n\tException={str(e)}"
                )
                self.logger.error(error_message)
                self._handle_fault(
                    error_message,
                    self.node_address,
                    CloseConnectionReason.SEND_MSG_FAILURE,
                )
            else:
                self.logger.warning(
                    "We have stopped already. We ignore that networkNode.sendMessage.onFailure call."
                )

        self._future.add_done_callback(FutureCallback(on_success, on_failure))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, GetBlocksResponse):
            if self._stopped:
                self.logger.warning(
                    "We have stopped already. We ignore that onDataRequest call."
                )
                return

            optional_node_address = connection.peers_node_address
            if not optional_node_address:
                self.logger.warning(
                    "Peers node address is not present, that is not expected."
                )
                # We do not return here as in case the connection has been created from the peers side we might not
                # have the address set. As we check the nonce later we do not care that much for the check if the
                # connection address is the same as the one we used.
            elif optional_node_address != self.node_address:
                self.logger.warning(
                    "Peers node address is not the same we used for the request. This is not expected. We ignore that message."
                )
                return

            get_blocks_response = network_envelope
            if get_blocks_response.request_nonce != self._nonce:
                self.logger.warning(
                    f"Nonce not matching. That can happen rarely if we get a response after a canceled "
                    f"handshake (timeout causes connection close but peer might have sent a msg before "
                    f"connection was closed).\n\t"
                    f"We drop that message. nonce={self._nonce} / requestNonce={get_blocks_response.request_nonce}"
                )
                return

            self.terminate()
            self.logger.info(
                f"\n#################################################################\n"
                f"We received from peer {self.node_address.get_full_address()} a BlocksResponse with {len(get_blocks_response.blocks)} blocks"
                f"\n#################################################################\n"
            )
            self._listener.on_complete(get_blocks_response)

    def terminate(self):
        self._stopped = True
        if self._future:
            self._future.cancel()
            self._future = None
        self._network_node.remove_message_listener(self)
        self._stop_timeout_timer()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _handle_fault(
        self,
        error_message: str,
        node_address: "NodeAddress",
        close_connection_reason: "CloseConnectionReason",
    ):
        self.terminate()
        self._peer_manager.handle_connection_fault(node_address=node_address)
        self._listener.on_fault(error_message, None)

    def _stop_timeout_timer(self):
        if self._timeout_timer is not None:
            self._timeout_timer.stop()
            self._timeout_timer = None
