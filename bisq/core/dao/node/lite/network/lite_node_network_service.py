from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import timedelta
import random
from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.dao.node.lite.network.request_blocks_handler import RequestBlocksHandler
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.peers.broadcaster import Broadcaster
from bisq.core.network.p2p.peers.peer_manager import PeerManager
from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
from utils.concurrency import ThreadSafeSet
from bisq.core.dao.node.messages.new_block_broadcast_message import (
    NewBlockBroadcastMessage,
)

if TYPE_CHECKING:
    from bisq.core.dao.node.messages.get_blocks_response import GetBlocksResponse
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.connection import Connection

logger = get_logger(__name__)


class LiteNodeNetworkService(MessageListener, ConnectionListener, PeerManager.Listener):
    """Responsible for requesting BSQ blocks from a full node and for listening to new blocks broadcasted by full nodes."""

    RETRY_DELAY_SEC = 10
    CLEANUP_TIMER_SEC = 120
    MAX_RETRY = 12

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    class Listener(ABC):
        @abstractmethod
        def on_no_seed_node_available(self):
            pass

        @abstractmethod
        def on_requested_blocks_received(
            self,
            get_blocks_response: "GetBlocksResponse",
            on_parsing_complete: Callable[[], None],
        ):
            pass

        @abstractmethod
        def on_new_block_received(
            self, new_block_broadcast_message: "NewBlockBroadcastMessage"
        ):
            pass

        @abstractmethod
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
        broadcaster: "Broadcaster",
        seed_nodes_repository: "SeedNodeRepository",
    ):
        self._network_node = network_node
        self._peer_manager = peer_manager
        self._broadcaster = broadcaster
        self._seed_node_addresses = set(seed_nodes_repository.get_seed_node_addresses())

        self._listeners = ThreadSafeSet["LiteNodeNetworkService.Listener"]()

        self._retry_counter = 0
        self._last_requested_block_height = 0
        self._last_received_block_height = 0

        # Key is tuple of seedNode address and requested blockHeight
        self._request_blocks_handler_map: dict[
            tuple["NodeAddress", int], "RequestBlocksHandler"
        ] = {}
        self._retry_timer: Optional["Timer"] = None
        self._stopped = False
        self._received_blocks = set[str]()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def start(self):
        self._network_node.add_message_listener(self)
        self._network_node.add_connection_listener(self)
        self._peer_manager.add_listener(self)

    def shut_down(self):
        self._stopped = True
        self._stop_retry_timer()
        self._network_node.remove_message_listener(self)
        self._network_node.remove_connection_listener(self)
        self._peer_manager.remove_listener(self)
        self._close_all_handlers()

    def add_listener(self, listener: "LiteNodeNetworkService.Listener"):
        self._listeners.add(listener)

    def request_blocks(self, start_block_height: int):
        """
        Args:
            start_block_height (int): Block height from where we expect new blocks (current block height in bsqState + 1).
        """

        self._last_requested_block_height = start_block_height
        connection_to_seed_node_optional = next(
            (
                conn
                for conn in self._network_node.get_confirmed_connections()
                if self._peer_manager.is_seed_node(conn)
            ),
            None,
        )

        if connection_to_seed_node_optional:
            candidate = connection_to_seed_node_optional.peers_node_address
            if candidate:
                self._seed_node_addresses.discard(candidate)
                self._request_blocks(candidate, start_block_height)
                return
        self._try_with_new_seed_node(start_block_height)

    def reset(self):
        self._last_requested_block_height = 0
        self._last_received_block_height = 0
        self._retry_counter = 0
        for handler in self._request_blocks_handler_map.values():
            handler.terminate()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ConnectionListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_connection(self, connection: "Connection"):
        pass

    def on_disconnect(
        self, close_connection_reason: "CloseConnectionReason", connection: "Connection"
    ):
        self._close_handler(connection)

        if self._peer_manager.is_peer_banned(close_connection_reason, connection):
            node_address_optional = connection.peers_node_address
            if node_address_optional:
                self._seed_node_addresses.discard(node_address_optional)
                self._remove_from_request_blocks_handler_map(node_address_optional)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PeerManager.Listener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_connections_lost(self):
        logger.info("on_all_connections_lost")
        self._close_all_handlers()
        self._stop_retry_timer()
        self._stopped = True
        self._try_with_new_seed_node(self._last_requested_block_height)

    def on_new_connection_after_all_connections_lost(self):
        logger.info("on_new_connection_after_all_connections_lost")
        self._close_all_handlers()
        self._stopped = False
        self._try_with_new_seed_node(self._last_requested_block_height)

    def on_awake_from_standby(self):
        logger.info("on_awake_from_standby")
        self._close_all_handlers()
        self._stopped = False
        self._try_with_new_seed_node(self._last_requested_block_height)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MessageListener implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        if isinstance(network_envelope, NewBlockBroadcastMessage):
            new_block_broadcast_message = network_envelope
            # We combine blockHash and txId list in case we receive blocks with different transactions.
            tx_ids = [tx.id for tx in new_block_broadcast_message.block.raw_txs]
            block_uid = f"{new_block_broadcast_message.block.hash}:{tx_ids}"
            if block_uid in self._received_blocks:
                logger.debug(
                    f"We had that message already and do not further broadcast it. blockUid={block_uid}"
                )
                return

            logger.info(
                f"We received a NewBlockBroadcastMessage from peer {connection.peers_node_address} and broadcast it to our peers. blockUid={block_uid}"
            )
            self._received_blocks.add(block_uid)
            self._broadcaster.broadcast(
                new_block_broadcast_message, connection.peers_node_address
            )
            for listener in self._listeners:
                listener.on_new_block_received(new_block_broadcast_message)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // RequestData
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _request_blocks(
        self, peers_node_address: "NodeAddress", start_block_height: int
    ):
        if self._stopped:
            logger.warning("We have stopped already. We ignore that requestData call.")
            return

        key = (peers_node_address, start_block_height)
        if key in self._request_blocks_handler_map:
            logger.warning(
                f"We have started already a requestDataHandshake for startBlockHeight {start_block_height} to peer. nodeAddress={peers_node_address}\n"
                "We start a cleanup timer if the handler has not closed by itself in between 2 minutes."
            )

            UserThread.run_after(
                lambda: self._cleanup_handler(key),
                timedelta(seconds=LiteNodeNetworkService.CLEANUP_TIMER_SEC),
            )
            return

        if start_block_height < self._last_received_block_height:
            logger.warning(
                f"startBlockHeight must not be smaller than lastReceivedBlockHeight. That should never happen. startBlockHeight={start_block_height}, lastReceivedBlockHeight={self._last_received_block_height}"
            )
            DevEnv.log_error_and_throw_if_dev_mode(
                f"startBlockHeight must be larger than lastReceivedBlockHeight. startBlockHeight={start_block_height} / lastReceivedBlockHeight={self._last_received_block_height}"
            )
            return

        request_blocks_handler = RequestBlocksHandler(
            self._network_node,
            self._peer_manager,
            peers_node_address,
            start_block_height,
            self._create_request_blocks_handler_listener(
                peers_node_address, start_block_height
            ),
        )
        self._request_blocks_handler_map[key] = request_blocks_handler
        request_blocks_handler.request_blocks()

    def _cleanup_handler(self, key: tuple["NodeAddress", int]):
        if key in self._request_blocks_handler_map:
            self._request_blocks_handler_map[key].terminate()
            self._request_blocks_handler_map.pop(key, None)

    def _create_request_blocks_handler_listener(
        self, peers_node_address: "NodeAddress", start_block_height: int
    ):
        class Listener(RequestBlocksHandler.Listener):
            def on_complete(listener_self, get_blocks_response: "GetBlocksResponse"):
                logger.info(f"requestBlocksHandler to {peers_node_address} completed")
                self._stop_retry_timer()

                # need to remove before listeners are notified as they cause the update call
                self._request_blocks_handler_map.pop(
                    (peers_node_address, start_block_height), None
                )
                # we only notify if our request was latest
                if start_block_height >= self._last_received_block_height:
                    self._last_received_block_height = start_block_height

                    for listener in self._listeners:
                        listener.on_requested_blocks_received(
                            get_blocks_response, lambda: None
                        )
                else:
                    logger.warning(
                        "We got a response which is already obsolete because we received a"
                        " response from a request with a higher block height."
                        " This could theoretically happen, but is very unlikely."
                    )

            def on_fault(
                listener_self,
                error_message: str,
                connection: Optional["Connection"] = None,
            ):
                logger.warning(
                    f"requestBlocksHandler with outbound connection failed.\n\tnodeAddress={peers_node_address}\n\tErrorMessage={error_message}"
                )

                self._peer_manager.handle_connection_fault(peers_node_address)
                self._request_blocks_handler_map.pop(
                    (peers_node_address, start_block_height), None
                )

                for listener in self._listeners:
                    listener.on_fault(error_message, connection)

                self._try_with_new_seed_node(start_block_height)

        return Listener()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _try_with_new_seed_node(self, start_block_height: int):
        if not self._network_node.get_all_connections():
            return

        if self._last_requested_block_height == 0:
            return

        if self._stopped:
            return

        if self._retry_timer:
            logger.warning("We have a retry timer already running.")
            return

        self._retry_counter += 1

        if self._retry_counter > LiteNodeNetworkService.MAX_RETRY:
            logger.warning(
                f"We tried {self._retry_counter} times but could not connect to a seed node."
            )
            for listener in self._listeners:
                listener.on_no_seed_node_available()
            return

        self._retry_timer = UserThread.run_after(
            lambda: self._retry_logic(start_block_height),
            timedelta(seconds=LiteNodeNetworkService.RETRY_DELAY_SEC),
        )

    def _retry_logic(self, start_block_height: int):
        self._stopped = False
        self._stop_retry_timer()

        candidate_list = [
            addr
            for addr in self._seed_node_addresses
            if self._peer_manager.is_seed_node(addr)
            and not self._peer_manager.is_self(addr)
        ]
        random.shuffle(candidate_list)

        if candidate_list:
            next_candidate = candidate_list[0]
            self._seed_node_addresses.remove(next_candidate)
            logger.info(
                f"We try requestBlocks from {next_candidate} with startBlockHeight={start_block_height}"
            )
            self._request_blocks(next_candidate, start_block_height)
        else:
            logger.warning("No more seed nodes available we could try.")
            for listener in self._listeners:
                listener.on_no_seed_node_available()

    def _stop_retry_timer(self):
        if self._retry_timer:
            self._retry_timer.stop()
            self._retry_timer = None

    def _close_handler(self, connection: "Connection"):
        node_address_optional = connection.peers_node_address
        if node_address_optional:
            self._remove_from_request_blocks_handler_map(node_address_optional)
        else:
            logger.trace(
                f"close_handler: nodeAddress not set in connection {connection}"
            )

    def _remove_from_request_blocks_handler_map(self, node_address: "NodeAddress"):
        handler_key = next(
            (key for key in self._request_blocks_handler_map if key[0] == node_address),
            None,
        )
        if handler_key:
            self._request_blocks_handler_map[handler_key].terminate()
            self._request_blocks_handler_map.pop(handler_key, None)

    def _close_all_handlers(self):
        for handler in self._request_blocks_handler_map.values():
            handler.terminate()
        self._request_blocks_handler_map.clear()
