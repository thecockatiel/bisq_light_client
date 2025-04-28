from abc import ABC, abstractmethod
from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.message_listener import MessageListener
from typing import TYPE_CHECKING, Optional
from bisq.core.network.p2p.peers.keepalive.messages.ping import Ping
from bisq.core.network.p2p.peers.keepalive.messages.pong import Pong
from utils.aio import FutureCallback
from utils.random import next_random_int
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope


class KeepAliveHandler(MessageListener):
    MAX_DELAY_MS = 10_000
    
    class Listener(ABC):
        @abstractmethod
        def on_complete(self_):
            pass
        
        @abstractmethod
        def on_fault(self_, error_message: str):
            pass
    
    def __init__(self, network_node: "NetworkNode", peer_manager: "PeerManager", listener: "Listener") -> None:
        super().__init__()
        self.logger = get_ctx_logger(__name__)
        self.network_node: "NetworkNode" = network_node
        self.peer_manager: "PeerManager" = peer_manager
        self.listener: "KeepAliveHandler.Listener" = listener
        self.nonce: int = next_random_int()
        self.connection: Optional["Connection"] = None
        self.stopped: bool = False
        self.delay_timer: Optional["Timer"] = None
        self.send_ts: int = 0

    def cancel(self) -> None:
        self.cleanup()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_ping_after_random_delay(self, connection: "Connection") -> None:
        # run randomly between 1 ms and 10 seconds
        self.delay_timer = UserThread.run_after_random_delay(lambda: self.send_ping(connection), timedelta(milliseconds=1), timedelta(milliseconds=KeepAliveHandler.MAX_DELAY_MS))

    def send_ping(self, connection: "Connection") -> None:
        if not self.stopped:
            ping = Ping(nonce=self.nonce, last_round_trip_time=connection.statistic.round_trip_time_property.value)
            self.send_ts = get_time_ms()
            
            future = self.network_node.send_message(connection, ping)                    

            def on_success(conn: "Connection"):
                if conn is None:
                    raise Exception("Future returned None, connection was expected")
                if not self.stopped:
                    self.connection = conn
                    conn.add_message_listener(self)
                else:
                    self.logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onSuccess call.")

            def on_failure(e):
                if not self.stopped:
                    error_message = (f"Sending ping to {connection} failed. That is expected if the peer is offline.\n"
                                f"\tping={ping}.\n\tException={str(e)}")
                    self.cleanup()
                    self.logger.info(error_message)
                    self.peer_manager.handle_connection_fault(connection=connection)
                    self.listener.on_fault(error_message)
                else:
                    self.logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onFailure call.")

            future.add_done_callback(FutureCallback(on_success, on_failure))
        else:
            self.logger.trace("We have stopped already. We ignore that sendPing call.")
            
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection") -> None:
        if isinstance(network_envelope, Pong):
            if not self.stopped:
                pong = network_envelope
                if pong.request_nonce == self.nonce:
                    round_trip_time = get_time_ms() - self.send_ts
                    connection.statistic.set_round_trip_time(round_trip_time)
                    self.cleanup()
                    self.listener.on_complete()
                else:
                    self.logger.warning("Nonce not matching. That should never happen.\n\t"
                              f"We drop that message. nonce={self.nonce} / requestNonce={pong.request_nonce}")
            else:
                self.logger.trace("We have stopped already. We ignore that onMessage call.")

    def cleanup(self) -> None:
        self.stopped = True
        if self.connection:
            self.connection.remove_message_listener(self)

        if self.delay_timer:
            self.delay_timer.stop()
            self.delay_timer = None