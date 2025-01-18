import asyncio
import socket
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from utils.aio import get_asyncio_loop
from socket import socket as Socket, error as SocketError
from typing import TYPE_CHECKING, Optional
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

async def sock_to_stream(sock: socket.socket) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    loop = get_asyncio_loop()
    
    reader = asyncio.StreamReader(loop=loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
    
    transport, _ = await loop.connect_accepted_socket(
        protocol,
        sock
    )
    
    writer = asyncio.StreamWriter(transport, protocol, reader, loop)
    
    return reader, writer

class Server:
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
        self.server_timer: Optional[Timer] = None

    def start(self):
        self.server_timer = UserThread.execute(self.run)
    
    async def run(self):
        try:
            if self.is_server_active():
                logger.debug(f"Ready to accept new clients on port {self.local_port}")
                client_socket, peer = await get_asyncio_loop().sock_accept(self.server_socket)
                reader, writer = await sock_to_stream(client_socket)

                logger.debug(
                    f"Accepted new client on localPort/port {client_socket.getsockname()[1]}/{peer[1]}"
                )

                connection = InboundConnection(
                    socket=(reader, writer),
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
                
                UserThread.execute(self.run)
        except SocketError as e:
            if self.is_server_active():
                logger.exception(e)
        except Exception as t:
            logger.error(f"Executing task failed. {str(t)}")
            logger.exception(t)

    def shut_down(self):
        logger.info("Server shutdown started")
        if self.is_server_active():
            if self.server_timer:
                self.server_timer.stop()

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
        return self.server_socket and not self.server_socket._closed
