from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Set
from concurrent.futures import Future
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_response import GetPeersResponse

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.peers.peerexchange.messages.get_peers_request import GetPeersRequest
    
logger = get_logger(__name__)

class GetPeersRequestHandler:
    # We want to keep timeout short here
    TIMEOUT_SEC = 90
    
    class Listener(ABC):
        @abstractmethod
        def on_complete():
            pass
        
        def on_fault(error_message: str, connection: "Connection"):
            pass
            
    def __init__(self, network_node: "NetworkNode", peer_manager: "PeerManager", listener: "GetPeersRequestHandler.Listener"):
        self.network_node = network_node
        self.peer_manager = peer_manager
        self.listener = listener
        self.timeout_timer: Optional[Timer] = None
        self.stopped: bool = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle(self, get_peers_request: "GetPeersRequest", connection: "Connection"):
        assert connection.peers_node_address, "The peers address must have been already set at the moment"
        
        get_peers_response = GetPeersResponse(
            request_nonce=get_peers_request.nonce,
            reported_peers=set(self.peer_manager.get_live_peers(connection.peers_node_address))
        )

        assert self.timeout_timer is None, "onGetPeersRequest must not be called twice."
        
        def timeout_handler():
            if not self.stopped:
                error_message = f"A timeout occurred at sending getPeersResponse:{get_peers_response} on connection:{connection}"
                logger.debug(error_message + " / PeerExchangeHandshake=" + str(self))
                logger.debug("timeoutTimer called. this=" + str(self))
                self.handle_fault(error_message, CloseConnectionReason.SEND_MSG_TIMEOUT, connection)
            else:
                logger.trace("We have stopped already. We ignore that timeoutTimer.run call.")
        
        self.timeout_timer = UserThread.run_after(timeout_handler, timedelta(seconds=self.TIMEOUT_SEC))

        future = self.network_node.send_message(connection, get_peers_response)
        
        def on_done(future: Future):
            try:
                future.result()
                if not self.stopped:
                    logger.trace("GetPeersResponse sent successfully")
                    self.cleanup()
                    self.listener.on_complete()
                else:
                    logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onSuccess call.")
            except Exception as e:
                if not self.stopped:
                    error_message = f"Sending getPeersResponse to {connection} failed. That is expected if the peer is offline. " \
                                f"getPeersResponse={get_peers_response}. Exception: {str(e)}"
                    logger.info(error_message)
                    self.handle_fault(error_message, CloseConnectionReason.SEND_MSG_FAILURE, connection)
                else:
                    logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onFailure call.")
        
        future.add_done_callback(on_done)
        
        self.peer_manager.add_to_reported_peers(
            get_peers_request.reported_peers,
            connection,
            get_peers_request.supported_capabilities,
        )

    def handle_fault(self, error_message: str, close_connection_reason: "CloseConnectionReason", connection: "Connection"):
        self.cleanup()
        self.listener.on_fault(error_message, connection)

    def cleanup(self):
        self.stopped = True
        if self.timeout_timer is not None:
            self.timeout_timer.stop()
            self.timeout_timer = None

