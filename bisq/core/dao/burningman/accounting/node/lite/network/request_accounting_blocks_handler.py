from bisq.core.dao.burningman.accounting.node.messages.get_accounting_blocks_request import (
    GetAccountingBlocksRequest,
)
from bisq.core.dao.burningman.accounting.node.messages.get_accounting_blocks_response import (
    GetAccountingBlocksResponse,
)
from utils.aio import FutureCallback
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.common.user_thread import UserThread
from utils.random import next_random_int

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.network.connection import Connection

logger = get_logger(__name__)


# Taken from RequestBlocksHandler
class RequestAccountingBlocksHandler(MessageListener):

    TIMEOUT_MIN = 3

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    class Listener:
        def on_complete(self, get_blocks_response: "GetAccountingBlocksResponse"):
            pass

        def on_fault(
            self, error_message: str, connection: Optional["Connection"] = None
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
        listener: "RequestAccountingBlocksHandler.Listener",
    ):
        self._network_node = network_node
        self._peer_manager = peer_manager
        self.node_address = node_address
        self.start_block_height = start_block_height
        self._listener = listener
        self._timeout_timer: Optional["Timer"] = None
        self._nonce = next_random_int()
        self._stopped = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_blocks(self):
        if self._stopped:
            logger.warning("We have stopped already. We ignore that requestData call.")
            return

        get_blocks_request = GetAccountingBlocksRequest(
            self.start_block_height,
            self._nonce,
            self._network_node.node_address_property.get(),
        )

        if self._timeout_timer is not None:
            logger.warning("We had a timer already running and stop it.")
            self._timeout_timer.stop()

        def handle_timeout():
            if not self._stopped:
                error_message = (
                    f"A timeout occurred when sending getAccountingBlocksRequest: {get_blocks_request} "
                    f"on peersNodeAddress: {self.node_address}"
                )
                logger.debug(f"{error_message} / RequestDataHandler={self}")
                self._handle_fault(
                    error_message,
                    self.node_address,
                    CloseConnectionReason.SEND_MSG_TIMEOUT,
                )
            else:
                logger.warning(
                    "We have stopped already. We ignore that timeoutTimer.run call. "
                    "Might be caused by a previous networkNode.sendMessage.onFailure."
                )

        # setup before sending to avoid race conditions (?)
        self._timeout_timer = UserThread.run_after(
            handle_timeout,
            timedelta(minutes=RequestAccountingBlocksHandler.TIMEOUT_MIN),
        )

        logger.info(
            f"\n\n>> We request blocks from peer {self.node_address.get_full_address()} from block height {get_blocks_request.from_block_height}.\n"
        )

        self._network_node.add_message_listener(self)

        future = self._network_node.send_message(self.node_address, get_blocks_request)

        def on_success(result):
            logger.debug(
                f"Sending of GetAccountingBlocksRequest message to peer {self.node_address.get_full_address()} succeeded."
            )

        def on_failure(e: Exception):
            if not self._stopped:
                error_message = (
                    f"Sending GetAccountingBlocksRequest to {self.node_address} failed. That is expected if the peer is offline.\n\t"
                    f"GetAccountingBlocksRequest={get_blocks_request}.\n\tException={str(e)}"
                )
                logger.error(error_message)
                self._handle_fault(
                    error_message,
                    self.node_address,
                    CloseConnectionReason.SEND_MSG_FAILURE,
                )
            else:
                logger.warning(
                    "We have stopped already. We ignore that networkNode.sendMessage.onFailure call."
                )

        future.add_done_callback(FutureCallback(on_success, on_failure))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, GetAccountingBlocksResponse):
            if self._stopped:
                logger.warning(
                    "We have stopped already. We ignore that onDataRequest call."
                )
                return

            optional_node_address = connection.peers_node_address
            if not optional_node_address:
                logger.warning(
                    "Peers node address is not present, that is not expected."
                )
                # We do not return here as in case the connection has been created from the peers side we might not
                # have the address set. As we check the nonce later we do not care that much for the check if the
                # connection address is the same as the one we used.
            elif optional_node_address != self.node_address:
                logger.warning(
                    "Peers node address is not the same we used for the request. This is not expected. We ignore that message."
                )
                return

            get_blocks_response = network_envelope
            if get_blocks_response.request_nonce != self._nonce:
                logger.warning(
                    f"Nonce not matching. That can happen rarely if we get a response after a canceled "
                    f"handshake (timeout causes connection close but peer might have sent a msg before "
                    f"connection was closed).\n\t"
                    f"We drop that message. nonce={self._nonce} / requestNonce={get_blocks_response.request_nonce}"
                )
                return

            self.terminate()
            logger.info(
                f"\n#################################################################\n"
                f"We received from peer {self.node_address.get_full_address()} a BlocksResponse with {len(get_blocks_response.blocks)} blocks"
                f"\n#################################################################\n"
            )
            self._listener.on_complete(get_blocks_response)

    def terminate(self):
        self._stopped = True
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
