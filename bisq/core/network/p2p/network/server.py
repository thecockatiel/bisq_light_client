from socket import socket as Socket, error as SocketError
import threading
from typing import TYPE_CHECKING
from collections.abc import Callable

from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.inbound_connection import InboundConnection
from bisq.common.setup.log_setup import get_logger
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.message_listener import MessageListener
    from bisq.core.network.p2p.network.connection_listener import ConnectionListener
    from bisq.common.protocol.network.network_proto_resolver import (
        NetworkProtoResolver,
    )
    from bisq.core.network.p2p.network.ban_filter import BanFilter
    from bisq.core.network.p2p.network.connection import Connection

logger = get_logger(__name__)


class Server(Callable[[], None]):
    def __init__(
        self,
        server_socket: Socket,
        message_listener: "MessageListener",
        connection_listener: "ConnectionListener",
        network_proto_resolver: "NetworkProtoResolver",
        ban_filter: "BanFilter" = None,
    ):
        self.server_socket = server_socket
        self.message_listener = message_listener
        self.connection_listener = connection_listener
        self.network_proto_resolver = network_proto_resolver
        self.ban_filter = ban_filter
        self.local_port = server_socket.getsockname()[1]
        self.connections: ThreadSafeSet["Connection"] = ThreadSafeSet()
        self.server_thread = threading.Thread(target=self)

    def start(self):
        self.server_thread.name = f"Server-{self.local_port}"
        self.server_thread.start()

    def __call__(self):
        try:
            while self.is_server_active():
                logger.debug(f"Ready to accept new clients on port {self.local_port}")
                client_socket, peer = self.server_socket.accept()

                if self.is_server_active():
                    logger.debug(
                        f"Accepted new client on localPort/port {client_socket.getsockname()[1]}/{peer[1]}"
                    )

                    connection = InboundConnection(
                        socket=client_socket,
                        message_listener=self.message_listener,
                        connection_listener=self.connection_listener,
                        network_proto_resolver=self.network_proto_resolver,
                        ban_filter=self.ban_filter,
                    )

                    logger.debug(
                        f"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                        f"Server created new inbound connection:\n"
                        f"localPort/port={self.server_socket.getsockname()[1]}/{client_socket.getpeername()[1]}\n"
                        f"connection.uid={connection.uid}\n"
                        f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                    )

                    if self.is_server_active():
                        self.connections.add(connection)
                    else:
                        connection.shut_down(CloseConnectionReason.APP_SHUT_DOWN)

        except SocketError as e:
            if self.is_server_active():
                logger.exception(e)
        except Exception as t:
            logger.error(f"Executing task failed. {str(t)}")
            logger.exception(t)

    def shut_down(self):
        logger.info("Server shutdown started")
        if self.is_server_active():
            self.server_thread.join(timeout=1.0)
            for connection in self.connections:
                connection.shut_down(CloseConnectionReason.APP_SHUT_DOWN)

            try:
                if not self.server_socket._closed:
                    self.server_socket.close()
            except SocketError as e:
                logger.debug(f"SocketException at shutdown might be expected {str(e)}")
            except Exception as e:
                logger.debug(f"Exception at shutdown. {str(e)}")
            finally:
                logger.debug("Server shutdown complete")
        else:
            logger.warning("stopped already called at shutdown")

    def is_server_active(self) -> bool:
        return self.server_thread.is_alive()
