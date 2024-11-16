from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from collections.abc import Callable
from dataclasses import dataclass
from copy import copy

from bisq.core.common.timer import Timer
from bisq.core.common.user_thread import UserThread
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.common.setup.log_setup import get_logger
from proto.pb_pb2 import NodeAddress
from utils.concurrency import ThreadSafeSet
from bisq.core.network.p2p.peers.broadcast_handler import BroadcastHandler

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.peers.peer_manager import PeerManager

logger = get_logger(__name__)

@dataclass(frozen=True)
class BroadcastRequest:
    message: 'BroadcastMessage'
    sender: Optional['NodeAddress'] = None
    listener: Optional['BroadcastHandler.Listener'] = None

class Broadcaster(BroadcastHandler.ResultHandler):
    BROADCAST_INTERVAL_MS = 2000

    def __init__(self, network_node: 'NetworkNode', peer_manager: 'PeerManager', max_connections: int):
        self.network_node = network_node
        self.peer_manager = peer_manager
        self.broadcast_handlers: ThreadSafeSet["BroadcastHandler"] = ThreadSafeSet()
        self.broadcast_requests: list["BroadcastRequest"] = []
        self.timer: Optional[Timer] = None
        self.shut_down_requested = False
        self.shut_down_result_handler: Optional[Callable[[], None]] = None
        
        # Create thread pool executor
        self.executor = ThreadPoolExecutor(
            max_workers=max_connections * 4,
            thread_name_prefix="Broadcaster"
        )

    def shut_down(self, result_handler: Callable[[], None]) -> None:
        logger.info("Broadcaster shutdown started")
        self.shut_down_requested = True
        self.shut_down_result_handler = result_handler
        
        if not self.broadcast_requests:
            self.do_shut_down()
        else:
            # We set delay of broadcasts and timeout to very low values,
            # so we can expect that we get on_completed called very fast and trigger the do_shut_down from there.
            self.maybe_broadcast_bundle()
        
        self.executor.shutdown()

    def flush(self) -> None:
        self.maybe_broadcast_bundle()

    def do_shut_down(self) -> None:
        logger.info("Broadcaster doShutDown started")
        for handler in self.broadcast_handlers:
            handler.cancel()
        if self.timer:
            self.timer.stop()
        if self.shut_down_result_handler:
            self.shut_down_result_handler()

    ###########################################################################################
    # API
    ###########################################################################################

    def broadcast(self, message: 'BroadcastMessage', 
                 sender: Optional['NodeAddress'] = None,
                 listener: Optional['BroadcastHandler.Listener'] = None):
        self.broadcast_requests.append(BroadcastRequest(message, sender, listener))
        if not self.timer:
            self.timer = UserThread.run_after(self.maybe_broadcast_bundle, timedelta(milliseconds=self.BROADCAST_INTERVAL_MS))

    def maybe_broadcast_bundle(self) -> None:
        if self.broadcast_requests:
            broadcast_handler = BroadcastHandler(self.network_node, self.peer_manager, self)
            self.broadcast_handlers.add(broadcast_handler)
            broadcast_handler.broadcast(copy(self.broadcast_requests), self.shut_down_requested, self.executor)
            self.broadcast_requests.clear()

            if self.timer:
                self.timer.stop()
            self.timer = None

    ###########################################################################################
    # BroadcastResultHandler implementation
    ###########################################################################################

    def on_completed(self, broadcast_handler: 'BroadcastHandler') -> None:
        self.broadcast_handlers.remove(broadcast_handler)
        if self.shut_down_requested:
            self.do_shut_down()