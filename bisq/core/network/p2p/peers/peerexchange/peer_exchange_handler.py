from abc import ABC, abstractmethod
from concurrent.futures import Future
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Set
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.message_listener import MessageListener
from utils.random import next_random_int
from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_request import GetPeersRequest
from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_response import GetPeersResponse
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason

if TYPE_CHECKING:
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    
logger = get_logger(__name__)

class PeerExchangeHandler(MessageListener):
    # We want to keep timeout short here
    TIMEOUT_SEC = 90
    DELAY_MS = 500
    
    class Listener(ABC):
        @abstractmethod
        def on_complete(self):
            pass
        
        @abstractmethod
        def on_fault(error_message: str, connection: Optional["Connection"]):
            pass

    def __init__(self, network_node: "NetworkNode", peer_manager: "PeerManager", listener: "PeerExchangeHandler.Listener"):
        self.network_node = network_node
        self.peer_manager = peer_manager
        self.listener = listener
        self.nonce = next_random_int()
        self.timeout_timer: "Timer" = None
        self.connection: Optional["Connection"] = None
        self.stopped = False
        self.delay_timer: "Timer" = None

    def cancel(self):
        self.cleanup() 

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_get_peers_request_after_random_delay(self, node_address: "NodeAddress"):
        self.delay_timer = UserThread.run_after_random_delay(
            lambda: self.send_get_peers_request(node_address),
            timedelta(milliseconds=1),
            timedelta(milliseconds=self.DELAY_MS)
        )

    def send_get_peers_request(self, node_address: "NodeAddress"):
        logger.debug(f"send_get_peers_request to node_address={node_address}")
        
        if self.stopped:
            logger.trace("We have stopped that handler already. We ignore that send_get_peers_request call.")
            return

        if self.network_node.node_address_property.value is None:
            logger.debug("My node address is still null at send_get_peers_request. We ignore that call.")
            return

        get_peers_request = GetPeersRequest(
            sender_node_address=self.network_node.node_address_property.value,
            nonce=self.nonce,
            reported_peers=set(self.peer_manager.get_live_peers(node_address))
        )

        if self.timeout_timer is None:
            #  setup before sending to avoid race conditions
            self.timeout_timer = UserThread.run_after(
                lambda: self._handle_timeout(node_address),
                timedelta(seconds=self.TIMEOUT_SEC)
            )
            
        def on_done(future: Future["Connection"]): 
            try:
                connection = future.result()
                if not connection:
                    raise Exception("Future returned None, connection was expected")
                if self.stopped:
                    logger.trace("We have stopped that handler already. We ignore that send_get_peers_request.on_success call.")
                    return
                self.connection = connection
                connection.add_message_listener(self) 
            except Exception as e:
                if self.stopped:
                    logger.trace("We have stopped that handler already. We ignore that send_get_peers_request.on_failure call.")
                    return
                
                error_message = (f"Sending get_peers_request to {node_address} failed. "
                            f"That is expected if the peer is offline. Exception={str(e)}")
                self._handle_fault(error_message, CloseConnectionReason.SEND_MSG_FAILURE, node_address)
                
        future = self.network_node.send_message(node_address, get_peers_request)
        future.add_done_callback(on_done)

    def _handle_timeout(self, node_address: "NodeAddress"):
        if not self.stopped:
            error_message = f"A timeout occurred at sending get_peers_request. node_address={node_address}"
            self._handle_fault(error_message, CloseConnectionReason.SEND_MSG_TIMEOUT, node_address)
        else:
            logger.trace("We have stopped that handler already. We ignore that timeout_timer.run call.")
            
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, GetPeersResponse):
            if not self.stopped:
                get_peers_response = network_envelope
                # Check if the response is for our request
                if get_peers_response.request_nonce == self.nonce:
                    self.peer_manager.add_to_reported_peers(
                        get_peers_response.reported_peers,
                        connection,
                        get_peers_response.supported_capabilities
                    )
                    self.cleanup()
                    self.listener.on_complete()
                else:
                    logger.warning(
                        f"Nonce not matching. That should never happen.\n\t"
                        f"We drop that message. nonce={self.nonce} / request_nonce={get_peers_response.request_nonce}"
                    )
            else:
                logger.trace("We have stopped that handler already. We ignore that on_message call.")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _handle_fault(self, error_message: str, close_connection_reason: "CloseConnectionReason", node_address: "NodeAddress"):
        self.cleanup()
        self.peer_manager.handle_connection_fault(node_address, self.connection)
        self.listener.on_fault(error_message, self.connection)

    def cleanup(self):
        self.stopped = True
        if self.connection is not None:
            self.connection.remove_message_listener(self)

        if self.timeout_timer is not None:
            self.timeout_timer.stop()
            self.timeout_timer = None

        if self.delay_timer is not None:
            self.delay_timer.stop()
            self.delay_timer = None

