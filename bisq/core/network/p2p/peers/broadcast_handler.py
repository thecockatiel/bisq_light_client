from datetime import timedelta
import uuid
from threading import Lock
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, Optional
from abc import ABC, abstractmethod
import random

from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.bundle_of_envelopes import BundleOfEnvelopes
from utils.concurrency import AtomicBoolean, AtomicInt, ThreadSafeSet

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.peers.broadcaster import BroadcastRequest
    from bisq.core.network.p2p.peers.peer_manager import PeerManager

logger = get_logger(__name__)


class BroadcastHandler:
    BASE_TIMEOUT_MS = 120 * 1000  # 120 seconds in milliseconds

    class ResultHandler(ABC):
        @abstractmethod
        def on_completed(self, broadcast_handler: "BroadcastHandler") -> None:
            pass

    class Listener(ABC):
        @abstractmethod
        def on_sufficiently_broadcast(
            self, broadcast_requests: list["BroadcastRequest"]
        ) -> None:
            pass

        @abstractmethod
        def on_not_sufficiently_broadcast(
            self, num_completed_broadcasts: int, num_failed_broadcast: int
        ) -> None:
            pass

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        result_handler: "ResultHandler",
    ):
        self._network_node = network_node
        self._peer_manager = peer_manager
        self._result_handler = result_handler
        self._uid = str(uuid.uuid4())

        self._stopped = AtomicBoolean(False)
        self._timeout_triggered = AtomicBoolean(False)
        self._num_completed_broadcasts = AtomicInt(0)
        self._num_failed_broadcasts = AtomicInt(0)
        self._num_peers_for_broadcast = AtomicInt(0)
        self._timeout_timer: Optional[Timer] = None
        self._send_message_futures: ThreadSafeSet[Future] = ThreadSafeSet()

        self._peer_manager.add_listener(self)

    def broadcast(
        self,
        broadcast_requests: list["BroadcastRequest"],
        shutdown_requested: bool,
        executor: "ThreadPoolExecutor",
    ):
        if not broadcast_requests:
            return

        confirmed_connections = list(self._network_node.get_confirmed_connections())
        random.shuffle(confirmed_connections)

        delay = 0
        if shutdown_requested:
            delay = 1
            # We sent to all peers as in case we had offers we want that it gets removed with higher reliability
            self._num_peers_for_broadcast.set(len(confirmed_connections))
        else:
            if self._requests_contain_own_message(broadcast_requests):
                # The broadcastRequests contains at least 1 message we have originated, so we send to all peers and
                # with shorter delay
                self._num_peers_for_broadcast.set(len(confirmed_connections))
                delay = 50
            else:
                # Relay nodes only send to max 7 peers and with longer delay
                self._num_peers_for_broadcast.set(min(7, len(confirmed_connections)))
                delay = 100

        self._setup_timeout_handler(broadcast_requests, delay, shutdown_requested)

        for i in range(self._num_peers_for_broadcast.get()):
            min_delay = (i + 1) * delay
            max_delay = (i + 2) * delay
            connection = confirmed_connections[i]

            def send_after_delay():
                if self._stopped:
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
                    if self._num_peers_for_broadcast.get() > 0:
                        self._num_peers_for_broadcast.decrement_and_get()
                    self._check_for_completion()
                    return

                if connection.stopped:
                    # Connection has died in the meantime. We skip it.
                    # We decrease numPeers in that case for making completion checks correct.
                    if self._num_peers_for_broadcast.get() > 0:
                        self._num_peers_for_broadcast.decrement_and_get()
                    self._check_for_completion()
                    return

                try:
                    self._send_to_peer(
                        connection, broadcast_requests_for_connection, executor
                    )
                except Exception as e:
                    logger.error(f"Exception at broadcast: {e}")
                    self._cleanup()

            UserThread.run_after_random_delay(
                send_after_delay,
                timedelta(milliseconds=min_delay),
                timedelta(milliseconds=max_delay),
            )

    def cancel(self) -> None:
        self._cleanup()

    def on_all_connections_lost(self) -> None:
        self._cleanup()

    def on_new_connection_after_all_connections_lost(self) -> None:
        pass

    def on_awake_from_standby(self) -> None:
        pass

    # Check if we have at least one message originated by ourselves
    def _requests_contain_own_message(
        self, broadcast_requests: list["BroadcastRequest"]
    ):
        my_address = self._network_node.node_address_property.value
        if not my_address:
            return False

        for broadcast_request in broadcast_requests:
            if broadcast_request.sender == my_address:
                return True
        return False

    def _setup_timeout_handler(
        self,
        broadcast_requests: list["BroadcastRequest"],
        delay: int,
        shut_down_requested: bool,
    ):
        # In case of shutdown we try to complete fast and set a short 1 second timeout
        base_timeout_ms = (
            1000 if shut_down_requested else BroadcastHandler.BASE_TIMEOUT_MS
        )
        timeout_delay = base_timeout_ms + delay * (
            self._num_peers_for_broadcast.get() + 1
        )  # We added 1 in the loop

        def timeout_handler():
            if self._stopped:
                return

            self._timeout_triggered.set(True)
            self._num_failed_broadcasts.increment_and_get()
            logger.warning(
                f"Broadcast did not complete after {timeout_delay / 1000} sec.\n"
                f"numPeersForBroadcast={self._num_peers_for_broadcast}\n"
                f"numOfCompletedBroadcasts={self._num_completed_broadcasts}\n"
                f"numOfFailedBroadcasts={self._num_failed_broadcasts}"
            )

            self._maybe_notify_listeners(broadcast_requests)
            self._cleanup()

        UserThread.run_after(timeout_handler, timedelta(milliseconds=timeout_delay))

    def _get_broadcast_requests_for_connection(
        self, connection: "Connection", broadcast_requests: list["BroadcastRequest"]
    ) -> list["BroadcastRequest"]:
        # We exclude the requests containing a message we received from that connection
        # Also we filter out messages which requires a capability but peer does not support it.
        return [
            broadcast_request
            for broadcast_request in broadcast_requests
            if not connection.peers_node_address
            or connection.peers_node_address != broadcast_request.sender
            and connection.test_capability(broadcast_request.message)
        ]

    def _send_to_peer(
        self,
        connection: "Connection",
        broadcast_requests_for_connection: list["BroadcastRequest"],
        executor: ThreadPoolExecutor,
    ):
        # Can be BundleOfEnvelopes or a single BroadcastMessage
        broadcast_message = self._get_message(broadcast_requests_for_connection)
        future = self._network_node.send_message(connection, broadcast_message)
        future.add_done_callback(
            lambda f: self._on_send_to_peer_completed(
                connection, broadcast_requests_for_connection, f
            )
        )

    def _on_send_to_peer_completed(
        self,
        connection: "Connection",
        broadcast_requests_for_connection: list["BroadcastRequest"],
        future: Future,
    ):
        try:
            future.result()  # check for success
            self._num_completed_broadcasts.increment_and_get()

            if self._stopped:
                return

            self._maybe_notify_listeners(broadcast_requests_for_connection)
            self._check_for_completion()
        except Exception as e:
            logger.warning(
                f"Broadcast to {connection.peers_node_address} failed. ",
                exc_info=(
                    e if not isinstance(e, (ConnectionError, BrokenPipeError)) else None
                ),
            )
            self._num_failed_broadcasts.increment_and_get()

            if self._stopped:
                return

            self._maybe_notify_listeners(broadcast_requests_for_connection)
            self._check_for_completion()

    def _get_message(self, broadcast_requests: list["BroadcastRequest"]):
        if len(broadcast_requests) == 1:
            # If we only have 1 message we avoid the overhead of the BundleOfEnvelopes and send the message directly
            return broadcast_requests[0].message
        else:
            return BundleOfEnvelopes(
                envelopes=[
                    broadcast_request.message
                    for broadcast_request in broadcast_requests
                ]
            )

    def _maybe_notify_listeners(self, broadcast_requests: list["BroadcastRequest"]):
        num_of_completed_broadcasts_target = max(
            1, min(self._num_peers_for_broadcast.get(), 3)
        )
        # We use equal checks to avoid duplicated listener calls as it would be the case with >= checks.
        if self._num_completed_broadcasts.get() == num_of_completed_broadcasts_target:
            # We have heard back from 3 peers (or all peers if numPeers is lower) so we consider the message was sufficiently broadcast.
            for broadcast_request in broadcast_requests:
                if broadcast_request.listener:
                    broadcast_request.listener.on_sufficiently_broadcast(
                        broadcast_requests
                    )
        else:
            # We check if number of open requests to peers is less than we need to reach numOfCompletedBroadcastsTarget.
            # Thus we never can reach required resilience as too many numOfFailedBroadcasts occurred.
            max_possible_success_cases = (
                self._num_peers_for_broadcast.get() - self._num_failed_broadcasts.get()
            )
            #  We subtract 1 as we want to have it called only once, with a < comparision we would trigger repeatedly.
            not_enough_succeeded_or_open = (
                max_possible_success_cases < num_of_completed_broadcasts_target - 1
            )
            #  We did not reach resilience level and timeout prevents to reach it later
            timeout_and_not_enough_succeeded = (
                self._timeout_triggered.set(True)
                and self._num_completed_broadcasts.get()
                < num_of_completed_broadcasts_target
            )
            if not_enough_succeeded_or_open or timeout_and_not_enough_succeeded:
                for broadcast_request in broadcast_requests:
                    if broadcast_request.listener:
                        broadcast_request.listener.on_not_sufficiently_broadcast(
                            self._num_completed_broadcasts.get(),
                            self._num_failed_broadcasts.get(),
                        )

    def _check_for_completion(self):
        if (
            self._num_completed_broadcasts.get() + self._num_failed_broadcasts.get()
            == self._num_peers_for_broadcast.get()
        ):
            self._cleanup()

    def _cleanup(self):
        if self._stopped:
            return

        self._stopped = True

        if self._timeout_timer:
            self._timeout_timer.stop()
            self._timeout_timer = None

        for future in self._send_message_futures:
            if not future.cancelled() and not future.done():
                future.cancel()
        self._send_message_futures.clear()

        self._peer_manager.remove_listener(self)
        self._result_handler.on_completed(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BroadcastHandler):
            return False
        return self._uid == other._uid

    def __hash__(self) -> int:
        return hash(self._uid)
