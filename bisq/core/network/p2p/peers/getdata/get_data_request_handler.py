from abc import ABC, abstractmethod
from concurrent.futures import Future
from datetime import timedelta
import time
from typing import TYPE_CHECKING

from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.common.setup.log_setup import get_logger
from utils.concurrency import AtomicBoolean
from utils.time import get_time_ms


if TYPE_CHECKING:
    from bisq.core.network.p2p.peers.getdata.messages.get_data_response import (
        GetDataResponse,
    )
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
    from bisq.core.network.p2p.network.connection import Connection
    from bisq.core.network.p2p.peers.getdata.messages.get_data_request import (
        GetDataRequest,
    )

logger = get_logger(__name__)


class GetDataRequestHandler:
    TIMEOUT_SEC = 240
    MAX_ENTRIES = 20_000  # Tradestatistics are about 20 000 in 2 months.

    class Listener(ABC):
        @abstractmethod
        def on_complete(self, serialized_size: int):
            pass

        @abstractmethod
        def on_fault(self, error_message: str, connection: "Connection"):
            pass

    def __init__(
        self,
        network_node: "NetworkNode",
        data_storage: "P2PDataStorage",
        listener: "Listener",
    ):
        self.network_node = network_node
        self.data_storage = data_storage
        self.listener = listener
        self.timeout_timer: "Timer" = None
        self.stopped = False

    def handle(self, get_data_request: "GetDataRequest", connection: "Connection"):
        ts = get_time_ms()
        connection_info = "connectionInfo"
        if connection.peers_node_address:
            connection_info += (
                " node address " + connection.peers_node_address.get_full_address()
            )
        else:
            connection_info += f" connection UID {connection.uid}"

        was_persistable_network_payloads_truncated = AtomicBoolean()
        was_protected_storage_entries_truncated = AtomicBoolean()
        data_response = self.data_storage.build_get_data_response(
            get_data_request,
            GetDataRequestHandler.MAX_ENTRIES,
            was_persistable_network_payloads_truncated,
            was_protected_storage_entries_truncated,
            connection.capabilities,
        )

        if was_persistable_network_payloads_truncated.get():
            logger.info(
                f"The getDataResponse for peer {connection_info} got truncated."
            )
        if was_protected_storage_entries_truncated.get():
            logger.info(
                f"The getDataResponse for peer {connection_info} got truncated."
            )

        logger.info(
            f"The getDataResponse to peer with {connection_info} contains {len(data_response.data_set)} ProtectedStorageEntries and {len(data_response.persistable_network_payload_set)} PersistableNetworkPayloads"
        )

        if self.timeout_timer is None:

            def on_timeout():
                error_message = f"A timeout occurred for getDataResponse on connection: {connection}"
                self._handle_fault(
                    error_message,
                    CloseConnectionReason.SEND_MSG_TIMEOUT,
                    connection,
                )

            self.timeout_timer = UserThread.run_after(
                on_timeout,
                timedelta(seconds=GetDataRequestHandler.TIMEOUT_SEC),
            )

        future = self.network_node.send_message(connection, data_response)
        future.add_done_callback(lambda f: self.on_future_complete(f, data_response))
        logger.info(f"handle GetDataRequest took {get_time_ms() - ts} ms")

    def stop(self):
        self._cleanup()

    def on_future_complete(
        self, future: "Future[Connection]", data_response: "GetDataResponse"
    ):
        try:
            connection = future.result()
            if not connection:
                raise Exception("Future returned None, connection was expected")
            if not self.stopped:
                logger.trace(
                    f"Send DataResponse to {connection.peers_node_address} succeeded. getDataResponse={data_response}"
                )
                self.listener.on_complete(
                    data_response.to_proto_network_envelope().ByteSize()
                )
                self._cleanup()
        except Exception as e:
            if not self.stopped:
                error_message = f"Sending getDataResponse to {connection} failed. That is expected if the peer is offline. getDataResponse={data_response}. Exception: {str(e)}"
                self._handle_fault(
                    error_message, CloseConnectionReason.SEND_MSG_FAILURE, connection
                )
            else:
                logger.trace("We have stopped already. We ignore that networkNode.sendMessage.onFailure call.")

    def _handle_fault(
        self,
        error_message: str,
        close_connection_reason: "CloseConnectionReason",
        connection: "Connection",
    ):
        if not self.stopped:
            logger.info(
                f"{error_message}\ncloseConnectionReason={close_connection_reason}"
            )
            self._cleanup()
            self.listener.on_fault(error_message, connection)
        else:
            logger.warning("We have already stopped (handleFault)")

    def _cleanup(self):
        self.stopped = True
        if self.timeout_timer is not None:
            self.timeout_timer.stop()
            self.timeout_timer = None
