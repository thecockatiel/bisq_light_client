from concurrent.futures import Future
from datetime import timedelta
import random
from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.outbound_connection import OutboundConnection
from bisq.core.network.p2p.peers.keepalive.messages.ping import Ping
from bisq.core.network.p2p.peers.keepalive.messages.pong import Pong
from bisq.core.network.p2p.peers.peer_manager import PeerManager

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.peers.keepalive.keep_alive_handler import KeepAliveHandler
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.connection import Connection

logger = get_logger(__name__)

class KeepAliveManager(MessageListener, ConnectionListener, PeerManager.Listener):
    INTERVAL_SEC = random.randint(0, 30) + 30
    LAST_ACTIVITY_AGE_MS = INTERVAL_SEC * 1000 / 2

    def __init__(self, network_node: "NetworkNode", peer_manager: PeerManager) -> None:
        self.network_node: "NetworkNode" = network_node
        self.peer_manager: PeerManager = peer_manager
        self.handler_map: dict[str, "KeepAliveHandler"] = {}
        
        self.stopped: bool = False
        self.keep_alive_timer: Optional["Timer"] = None

        self.network_node.add_message_listener(self)
        self.network_node.add_connection_listener(self)
        self.peer_manager.add_listener(self)

    def shut_down(self) -> None:
        self.stopped = True
        self.network_node.remove_message_listener(self)
        self.network_node.remove_connection_listener(self)
        self.peer_manager.remove_listener(self)
        self.close_all_handlers()
        self.stop_keep_alive_timer()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def start(self) -> None:
        self.restart()
        

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection") -> None:
        if isinstance(network_envelope, Ping):
            if self.stopped:
                ping = network_envelope
                
                # We get from peer last measured rrt
                connection.statistic.set_round_trip_time(ping.last_round_trip_time)

                pong = Pong(ping.nonce)
                future = self.network_node.send_message(connection, pong)
                future.add_done_callback(lambda f: self._handle_pong_failure(f, connection))
            else:
                logger.warning("We have stopped already. We ignore that onMessage call.")

    def _handle_pong_failure(self, future: "Future", connection: "Connection") -> None:
        try: 
            future.result()
        except Exception as e:
            if not self.stopped:
                logger.info(f"Sending pong to {connection} failed. That is expected if the "
                            f"peer is offline. Exception: {str(e)}")
                self.peer_manager.handle_connection_fault(connection)
            else:
                logger.warning("We have stopped already. We ignore that  networkNode.sendMessage.onFailure call.")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def on_connection(self, connection: Connection):
        pass
    
    def on_disconnect(self, close_connection_reason: CloseConnectionReason, connection: Connection):
        self.close_handler(connection)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PeerManager.Listener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_connections_lost(self) -> None:
        self.close_all_handlers()
        self.stop_keep_alive_timer()
        self.stopped = True
        self.restart()

    def on_new_connection_after_all_connections_lost(self) -> None:
        self.close_all_handlers()
        self.stopped = False
        self.restart()

    def on_awake_from_standby(self) -> None:
        self.close_all_handlers()
        self.stopped = False
        if self.network_node.get_all_connections():
            self.restart()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def restart(self) -> None:
        if self.keep_alive_timer is None:
            def keep_alive_task():
                self.stopped = False
                self.keep_alive()
            
            self.keep_alive_timer = UserThread.run_periodically(keep_alive_task, timedelta(self.INTERVAL_SEC))

    def keep_alive(self) -> None:
        if not self.stopped:
            for connection in self.network_node.get_confirmed_connections():
                if (isinstance(connection, OutboundConnection) and 
                        connection.statistic.get_last_activity_age() > self.LAST_ACTIVITY_AGE_MS):
                    uid = connection.uid
                    if uid not in self.handler_map:
                        class KeepAliveListener(KeepAliveHandler.Listener):
                            def __init__(self, manager: "KeepAliveManager", connection_uid: str):
                                self.manager = manager
                                self.uid = connection_uid
                            
                            def on_complete(self):
                                self.manager.handler_map.pop(self.uid, None)
                            
                            def on_fault(self, error_message):
                                self.manager.handler_map.pop(self.uid, None)

                        keep_alive_handler = KeepAliveHandler(
                            self.network_node, 
                            self.peer_manager,
                            KeepAliveListener(self, uid)
                        )
                        self.handler_map[uid] = keep_alive_handler
                        keep_alive_handler.send_ping_after_random_delay(connection)
                    else:
                        # TODO check if this situation causes any issues
                        logger.debug(f"Connection with id {uid} has not completed and is still in our map. "
                                   f"We will try to ping that peer at the next schedule.")

            size = len(self.handler_map)
            logger.debug(f"handlerMap size={size}")
            if size > self.peer_manager.get_max_connections():
                logger.warning(f"Seems we didn't clean up out map correctly.\n"
                             f"handlerMap size={size}, peerManager.getMaxConnections()="
                             f"{self.peer_manager.get_max_connections()}")
        else:
            logger.warning("We have stopped already. We ignore that keepAlive call.")

    def stop_keep_alive_timer(self) -> None:
        self.stopped = True
        if self.keep_alive_timer is not None:
            self.keep_alive_timer.stop()
            self.keep_alive_timer = None

    def close_handler(self, connection: "Connection") -> None:
        uid = connection.uid
        if uid in self.handler_map:
            self.handler_map[uid].cancel()
            del self.handler_map[uid]

    def close_all_handlers(self) -> None:
        for handler in self.handler_map.values():
            handler.cancel()
        self.handler_map.clear()

