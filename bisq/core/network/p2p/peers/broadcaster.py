from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional
from collections.abc import Callable
from dataclasses import dataclass

from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from utils.concurrency import ThreadSafeSet
from bisq.core.network.p2p.peers.broadcast_handler import BroadcastHandler

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.peers.peer_manager import PeerManager



@dataclass(frozen=True)
class BroadcastRequest:
    message: "BroadcastMessage"
    sender: Optional["NodeAddress"] = None
    listener: Optional["BroadcastHandler.Listener"] = None


class Broadcaster(BroadcastHandler.ResultHandler):
    BROADCAST_INTERVAL_MS = 2000

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        max_connections: int,
    ):
        self.logger = get_ctx_logger(__name__)
        self._network_node = network_node
        self._peer_manager = peer_manager
        self._broadcast_handlers: ThreadSafeSet["BroadcastHandler"] = ThreadSafeSet()
        self._broadcast_requests: list["BroadcastRequest"] = []
        self._timer: Optional[Timer] = None
        self._shut_down_requested = False
        self._shut_down_result_handler: Optional[Callable[[], None]] = None

        # Create thread pool executor
        self._executor = ThreadPoolExecutor(
            max_workers=max_connections * 4, thread_name_prefix="Broadcaster"
        )

    def shut_down(self, result_handler: Callable[[], None]) -> None:
        self.logger.info("Broadcaster shutdown started")
        self._shut_down_requested = True
        self._shut_down_result_handler = result_handler

        if not self._broadcast_requests:
            self.do_shut_down()
        else:
            # We set delay of broadcasts and timeout to very low values,
            # so we can expect that we get on_completed called very fast and trigger the do_shut_down from there.
            self.maybe_broadcast_bundle()

        self._executor.shutdown()

    def flush(self) -> None:
        self.maybe_broadcast_bundle()

    def do_shut_down(self) -> None:
        self.logger.info("Broadcaster doShutDown started")
        for handler in self._broadcast_handlers:
            handler.cancel()
        if self._timer:
            self._timer.stop()
        if self._shut_down_result_handler:
            self._shut_down_result_handler()

    ###########################################################################################
    # API
    ###########################################################################################

    def broadcast(
        self,
        message: "BroadcastMessage",
        sender: Optional["NodeAddress"] = None,
        listener: Optional["BroadcastHandler.Listener"] = None,
    ):
        self._broadcast_requests.append(BroadcastRequest(message, sender, listener))
        if not self._timer:
            self._timer = UserThread.run_after(
                self.maybe_broadcast_bundle,
                timedelta(milliseconds=Broadcaster.BROADCAST_INTERVAL_MS),
            )

    def maybe_broadcast_bundle(self) -> None:
        if self._broadcast_requests:
            broadcast_handler = BroadcastHandler(
                self._network_node, self._peer_manager, self
            )
            self._broadcast_handlers.add(broadcast_handler)
            broadcast_handler.broadcast(
                self._broadcast_requests.copy(),
                self._shut_down_requested,
                self._executor,
            )
            self._broadcast_requests.clear()

            if self._timer:
                self._timer.stop()
            self._timer = None

    ###########################################################################################
    # BroadcastResultHandler implementation
    ###########################################################################################

    def on_completed(self, broadcast_handler: "BroadcastHandler") -> None:
        self._broadcast_handlers.discard(broadcast_handler)
        if self._shut_down_requested:
            self.do_shut_down()
