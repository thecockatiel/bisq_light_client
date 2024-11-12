from datetime import timedelta
import logging
import uuid
from threading import Lock
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, List, Set, Optional
from abc import ABC, abstractmethod
import random

from bisq.core.common.timer import Timer
from bisq.core.common.user_thread import UserThread
from bisq.core.network.p2p.bundle_of_envelopes import BundleOfEnvelopes
from bisq.core.network.p2p.peers.broadcaster import BroadcastRequest
from bisq.core.network.p2p.peers.peer_manager import PeerManager
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.network.connection import Connection

logger = logging.getLogger(__name__)


class BroadcastResultHandler(ABC):
    @abstractmethod
    def on_completed(self, broadcast_handler: "BroadcastHandler") -> None:
        pass


class BroadcastListener(ABC):
    @abstractmethod
    def on_sufficiently_broadcast(
        self, broadcast_requests: List["BroadcastRequest"]
    ) -> None:
        pass

    @abstractmethod
    def on_not_sufficiently_broadcast(
        self, num_completed_broadcasts: int, num_failed_broadcast: int
    ) -> None:
        pass


class BroadcastHandler:
    BASE_TIMEOUT_MS = 120 * 1000  # 120 seconds in milliseconds

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        result_handler: "BroadcastResultHandler",
    ):
        self.network_node = network_node
        self.peer_manager = peer_manager
        self.result_handler = result_handler
        self.uid = str(uuid.uuid4())

        self.stopped = False
        self.timeout_triggered = False
        self.num_completed_broadcasts = 0
        self.num_failed_broadcasts = 0
        self.num_peers_for_broadcast = 0
        self.timeout_timer: Optional[Timer] = None
        self.send_message_futures: ThreadSafeSet[Future] = ThreadSafeSet()
        self._lock = Lock()

        self.peer_manager.add_listener(self)

    def broadcast(
        self,
        broadcast_requests: List["BroadcastRequest"],
        shutdown_requested: bool,
        executor: ThreadPoolExecutor,
    ):
        if not broadcast_requests:
            return

        confirmed_connections = list(self.network_node.get_confirmed_connections())
        random.shuffle(confirmed_connections)

        delay = 0
        if shutdown_requested:
            delay = 1
            # We sent to all peers as in case we had offers we want that it gets removed with higher reliability
            self.num_peers_for_broadcast = len(confirmed_connections)
        else:
            if self._requests_contain_own_message(broadcast_requests):
                # The broadcastRequests contains at least 1 message we have originated, so we send to all peers and
                # with shorter delay
                self.num_peers_for_broadcast = len(confirmed_connections)
                delay = 50
            else:
                # Relay nodes only send to max 7 peers and with longer delay
                self.num_peers_for_broadcast = min(7, len(confirmed_connections))
                delay = 100

        self._setup_timeout_handler(broadcast_requests, delay, shutdown_requested)

        for i in range(self.num_peers_for_broadcast):
            min_delay = (i + 1) * delay
            max_delay = (i + 2) * delay
            connection = confirmed_connections[i]

            def send_after_delay():
                if self.stopped:
                    return

                # We use broadcastRequests which have excluded the requests for messages the connection has
                # originated to avoid sending back the message we received. We also remove messages not satisfying
                # capability checks.
                broadcast_requests_for_connection = (
                    self._get_broadcast_requests_for_connection(
                        connection, broadcast_requests
                    )
                )

                # Could be empty list...
                if not broadcast_requests_for_connection:
                    # We decrease numPeers in that case for making completion checks correct.
                    if self.num_peers_for_broadcast > 0:
                        self.num_peers_for_broadcast -= 1
                    self._check_for_completion()
                    return

                if connection.stopped:
                    # Connection has died in the meantime. We skip it.
                    # We decrease numPeers in that case for making completion checks correct.
                    if self.num_peers_for_broadcast > 0:
                        self.num_peers_for_broadcast -= 1
                    self._check_for_completion()
                    return

                try:
                    self._send_to_peer(
                        connection, broadcast_requests_for_connection, executor
                    )
                except Exception as e:
                    logger.error(f"Exception at broadcast: {e}")
                    self._cleanup()

            UserThread.run_after_random_delay(send_after_delay, min_delay, max_delay)

    def cancel(self) -> None:
        self._cleanup()

    def on_all_connections_lost(self) -> None:
        self._cleanup()

    def on_new_connection_after_all_connections_lost(self) -> None:
        pass

    def on_awake_from_standby(self) -> None:
        pass

    # Check if we have at least one message originated by ourselves
    def _requests_contain_own_message(self, broadcast_requests: List["BroadcastRequest"]):
        my_address = self.network_node.node_address
        if not my_address:
            return False

        for broadcast_request in broadcast_requests:
            if broadcast_request.sender == my_address:
                return True
        return False
    
    def _setup_timeout_handler(self, broadcast_requests: List["BroadcastRequest"], delay: int, shut_down_requested: bool):
        # In case of shutdown we try to complete fast and set a short 1 second timeout
        base_timeout_ms = 1000 if shut_down_requested else self.BASE_TIMEOUT_MS
        timeout_delay = base_timeout_ms + delay * (self.num_peers_for_broadcast + 1) # We added 1 in the loop
        def timeout_handler():
            if self.stopped:
                return

            self.timeout_triggered = True
            self.num_failed_broadcasts += 1
            logger.warning(
                f"Broadcast did not complete after {timeout_delay / 1000} sec.\n"
                f"numPeersForBroadcast={self.num_peers_for_broadcast}\n"
                f"numOfCompletedBroadcasts={self.num_completed_broadcasts}\n"
                f"numOfFailedBroadcasts={self.num_failed_broadcasts}"
            )

            self._maybe_notify_listeners(broadcast_requests)
            self._cleanup()
        UserThread.run_after(timeout_handler, timedelta(milliseconds=timeout_delay))
    
    def _get_broadcast_requests_for_connection(self, connection: "Connection", broadcast_requests: List["BroadcastRequest"]) -> List["BroadcastRequest"]:
        # We exclude the requests containing a message we received from that connection
        # Also we filter out messages which requires a capability but peer does not support it.
        return [
            broadcast_request
            for broadcast_request in broadcast_requests
            if not connection.peers_node_address or connection.peers_node_address != broadcast_request.sender
            and connection.test_capability(broadcast_request.message)
        ]
    
    def _send_to_peer(self, connection: "Connection", broadcast_requests_for_connection: List["BroadcastRequest"], executor: ThreadPoolExecutor):
        # Can be BundleOfEnvelopes or a single BroadcastMessage
        broadcast_message = self._get_message(broadcast_requests_for_connection)
        future = self.network_node.send_message(connection, broadcast_message)
        future.add_done_callback(lambda: self._on_send_to_peer_completed(connection, broadcast_requests_for_connection, future))
    
    def _on_send_to_peer_completed(self, connection: "Connection", broadcast_requests_for_connection: List["BroadcastRequest"], future: Future):
        if future.done() and not future.cancelled():
            self.num_completed_broadcasts += 1
            
            if self.stopped:
                return
            
            self._maybe_notify_listeners(broadcast_requests_for_connection)
            self._check_for_completion()
        else:
            exc_info = None
            try:
                exc_info=future.exception()
            except:
                pass
            logger.warning("Broadcast to " + connection.peers_node_address + " failed. ", exc_info=exc_info)
            self.num_failed_broadcasts += 1
            
            if self.stopped:
                return
            
            self._maybe_notify_listeners(broadcast_requests_for_connection)
            self._check_for_completion()
            
        
    def _get_message(self, broadcast_requests: List["BroadcastRequest"]):
        if len(broadcast_requests) == 1:
            # If we only have 1 message we avoid the overhead of the BundleOfEnvelopes and send the message directly
            return broadcast_requests[0].message
        else:
            return BundleOfEnvelopes([broadcast_request.message for broadcast_request in broadcast_requests])
        
    def _maybe_notify_listeners(self, broadcast_requests: List["BroadcastRequest"]):
        num_of_completed_broadcasts_target = max(1, min(self.num_peers_for_broadcast, 3))
        # We use equal checks to avoid duplicated listener calls as it would be the case with >= checks.
        if self.num_completed_broadcasts == num_of_completed_broadcasts_target:
            # We have heard back from 3 peers (or all peers if numPeers is lower) so we consider the message was sufficiently broadcast.
            for broadcast_request in broadcast_requests:
                if broadcast_request.listener:
                    broadcast_request.listener.on_sufficiently_broadcast(broadcast_requests)
        else:
            # We check if number of open requests to peers is less than we need to reach numOfCompletedBroadcastsTarget.
            # Thus we never can reach required resilience as too many numOfFailedBroadcasts occurred.
            max_possible_success_cases = self.num_peers_for_broadcast - self.num_failed_broadcasts
            #  We subtract 1 as we want to have it called only once, with a < comparision we would trigger repeatedly.
            not_enough_succeeded_or_open = max_possible_success_cases < num_of_completed_broadcasts_target - 1
            #  We did not reach resilience level and timeout prevents to reach it later
            timeout_and_not_enough_succeeded = self.timeout_triggered and self.num_completed_broadcasts < num_of_completed_broadcasts_target
            if not_enough_succeeded_or_open or timeout_and_not_enough_succeeded:
                for broadcast_request in broadcast_requests:
                    if broadcast_request.listener:
                        broadcast_request.listener.on_not_sufficiently_broadcast(self.num_completed_broadcasts, self.num_failed_broadcasts)
    
    def _check_for_completion(self):
        if self.num_completed_broadcasts + self.num_failed_broadcasts == self.num_peers_for_broadcast:
            self._cleanup()
            
    def _cleanup(self):
        if self.stopped:
            return
        
        self.stopped = True
        
        if self.timeout_timer:
            self.timeout_timer.stop()
            self.timeout_timer = None
        
        for future in self.send_message_futures:
            if not future.cancelled() and not future.done():
                future.cancel()
        self.send_message_futures.clear()
        
        self.peer_manager.remove_listener(self)
        self.result_handler.on_completed(self)
            
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BroadcastHandler):
            return False
        return self.uid == other.uid
    
    def __hash__(self) -> int:
        return hash(self.uid)