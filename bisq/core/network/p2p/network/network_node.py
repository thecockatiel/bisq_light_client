from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from socket import socket as Socket
import threading
from typing import TYPE_CHECKING, Callable, Optional, Set
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.common.protocol.network.network_proto_resolver import (
    NetworkProtoResolver,
)
from bisq.core.common.timer import Timer
from bisq.core.common.user_thread import UserThread
from bisq.core.network.p2p.network.ban_filter import BanFilter
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection import Connection
from bisq.core.network.p2p.network.message_listener import MessageListener
from bisq.core.network.p2p.network.outbound_connection import OutboundConnection
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.p2p.network.socks5_proxy_internal_factory import (
    Socks5ProxyInternalFactory,
)
from bisq.core.network.p2p.network.server import Server
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.logging import get_logger
from utils.concurrency import ThreadSafeSet
from utils.formatting import to_truncated_string
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.setup_listener import SetupListener
    from bisq.core.network.p2p.network.inbound_connection import InboundConnection
    from bisq.core.network.p2p.network.connection_listener import ConnectionListener
    from bisq.core.common.capabilities import Capabilities

logger = get_logger(__name__)


class NetworkNode(MessageListener, Socks5ProxyInternalFactory, ABC):
    CREATE_SOCKET_TIMEOUT = 120 * 1000

    def __init__(
        self,
        service_port: int,
        network_proto_resolver: NetworkProtoResolver,
        ban_filter: Optional[BanFilter],
        max_connections: int,
    ):
        self.service_port = service_port
        self.network_proto_resolver = network_proto_resolver
        self.ban_filter = ban_filter

        self.inbound_connections: ThreadSafeSet["InboundConnection"] = ThreadSafeSet()
        self.message_listeners: ThreadSafeSet["MessageListener"] = ThreadSafeSet()
        self.connection_listeners: ThreadSafeSet["ConnectionListener"] = ThreadSafeSet()
        self.setup_listeners: ThreadSafeSet["SetupListener"] = ThreadSafeSet()

        self.connection_executor = ThreadPoolExecutor(max_workers=max_connections * 2)
        self.send_message_executor = ThreadPoolExecutor(max_workers=max_connections * 3)

        self.shut_down_in_progress = False
        self.outbound_connections: ThreadSafeSet[OutboundConnection] = ThreadSafeSet()
        self.node_address: NodeAddress = None
        self.server: Server = None

    @abstractmethod
    def start(self, setup_listener: Optional["SetupListener"] = None):
        pass

    def _send_message(self, connection: Connection, network_envelope: NetworkEnvelope):
        if connection is None:
            logger.error("Connection is null. We can not send the message.")
            return
        if network_envelope is None:
            logger.error("NetworkEnvelope is null. We can not send the message.")
            return
        id = (
            connection.peers_node_address.get_full_address()
            if connection.peers_node_address
            else connection.uid
        )
        threading.current_thread().setName(
            f"NetworkNode:SendMessage-to-{to_truncated_string(id, 15)}"
        )
        connection.send_message(network_envelope)

        return connection

    def _make_connection(
        self, peers_node_address: NodeAddress, network_envelope: NetworkEnvelope
    ):
        if peers_node_address is None:
            raise ValueError("peers_node_address must not be null")
        threading.current_thread().setName(
            f"NetworkNode.connectionExecutor:SendMessage-to-{to_truncated_string(peers_node_address.get_full_address(), 15)}"
        )
        if peers_node_address == self.node_address:
            logger.warning("We are sending a message to ourselves")

        startTs = get_time_ms()

        logger.debug(f"Start create socket to {peers_node_address.get_full_address()}")

        socket: Socket = self.createSocket(peers_node_address)

        duration = get_time_ms() - startTs
        logger.info(
            f"Socket creation to peersNodeAddress {peers_node_address.get_full_address()} took {duration} ms"
        )

        if duration > NetworkNode.CREATE_SOCKET_TIMEOUT:
            raise TimeoutError("A timeout occurred when creating a socket.")

        # Tor needs sometimes quite long to create a connection. To avoid that we get too many
        # connections with the same peer we check again if we still don't have any connection for that node address.
        existing_connection = self.get_inbound_connection(peers_node_address)
        if existing_connection is None:
            existing_connection = self.get_outbound_connection(peers_node_address)

        if existing_connection is not None:
            logger.debug(
                f"We found in the meantime a connection for peers_node_address {peers_node_address.get_full_address()}, "
                "so we use that for sending the message.\n"
                "That can happen if Tor needs long for creating a new outbound connection.\n"
                "We might have got a new inbound or outbound connection."
            )
            try:
                socket.close()
            except:
                if not self.shut_down_in_progress:
                    logger.error("Error at closing socket", exc_info=True)

            existing_connection.send_message(network_envelope)
            return existing_connection
        else:
            outbound_connection = OutboundConnection(
                socket=socket,
                message_listener=self,
                connection_listener=NetworkNodeOutboundConnectionListener(self),
                peers_node_address=peers_node_address,
                network_proto_resolver=self.network_proto_resolver,
                ban_filter=self.ban_filter,
            )
            logger.debug(
                f"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                + "NetworkNode created new outbound connection:\n"
                + "my_node_address="
                + self.node_address
                + "\n"
                + "peers_node_address="
                + peers_node_address
                + "\n"
                + "uid="
                + outbound_connection.uid
                + "\n"
                + "message="
                + network_envelope
                + "\n"
                + f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
            )
            # can take a while when using tor
            outbound_connection.send_message(network_envelope)
            return outbound_connection

    def send_message(
        self, peers_node_address: NodeAddress, network_envelope: NetworkEnvelope
    ):
        logger.debug(
            f"Send {network_envelope.__class__.__name__} to {peers_node_address}. Message details: {network_envelope}"
        )

        if not isinstance(peers_node_address, NodeAddress):
            raise ValueError("peerAddress must not be null")

        connection = self.get_outbound_connection(peers_node_address)

        if not connection:
            connection = self.get_inbound_connection(peers_node_address)

        if connection:
            try:
                return self.send_message_executor.submit(
                    self._send_message, connection, network_envelope
                )
            except Exception as e:
                logger.error(
                    "Error when submitting _send_message task to send_message_executor",
                    exc_info=e,
                )
                raise
        else:
            logger.debug(
                f"We have not found any connection for peerAddress {peers_node_address}.\n\t"
                "We will create a new outbound connection."
            )

            try:
                return self.connection_executor.submit(
                    self._make_connection, peers_node_address, network_envelope
                )
            except Exception as e:
                logger.error(
                    "Error when submitting _make_connection task to connection_executor",
                    exc_info=e,
                )
                raise

    def lookup_outbound_connection(self, peers_node_address: NodeAddress):
        logger.debug(
            f"lookupOutboundConnection for peersNodeAddress={peers_node_address.get_full_address()}"
        )
        self.print_outbound_connections()

        for connection in self.outbound_connections:
            if (
                connection.peers_node_address
                and peers_node_address == connection.peers_node_address
            ):
                return connection

        return None

    def lookup_inbound_connection(self, peers_node_address: NodeAddress):
        full_address = peers_node_address.get_full_address()
        logger.debug("lookupInboundConnection for peersNodeAddress=", full_address)
        self.print_inbound_connections()

        return next(
            (
                connection
                for connection in self.inbound_connections
                if connection.peers_node_address
                and connection.peers_node_address.get_full_address() == full_address
            ),
            None,
        )

    def print_outbound_connections(self):
        sb = f"outBoundConnections len()={len(self.outbound_connections)}\n\toutBoundConnections="
        for connection in self.outbound_connections:
            sb += f"{connection}\n\t"
        logger.debug(sb)

    def print_inbound_connections(self):
        sb = f"inBoundConnections len()={len(self.inbound_connections)}\n\toutBoundConnections="
        for connection in self.outbound_connections:
            sb += f"{connection}\n\t"
        logger.debug(sb)

    def get_inbound_connection(
        self, peers_node_address: NodeAddress
    ) -> Optional[InboundConnection]:
        inbound_connection_optional = self.lookup_inbound_connection(
            str(peers_node_address)
        )
        if inbound_connection_optional is not None:
            connection = inbound_connection_optional
            print(
                f"We have found a connection in inBoundConnections. Connection.uid={connection.get_uid()}"
            )
            if connection.is_stopped():
                print(
                    f"We have a connection which is already stopped in inBoundConnections. Connection.uid={connection.get_uid()}"
                )
                # Assuming 'in_bound_connections' is a global or class variable
                global in_bound_connections
                in_bound_connections.remove(connection)
                return None
            else:
                return connection
        else:
            return None

    def get_outbound_connection(
        self, peers_node_address: NodeAddress
    ) -> Optional[OutboundConnection]:
        outbound_connection_optional = self.lookup_outbound_connection(
            str(peers_node_address)
        )
        if outbound_connection_optional is not None:
            connection = outbound_connection_optional
            print(
                f"We have found a connection in outBoundConnections. Connection.uid={connection.get_uid()}"
            )
            if connection.is_stopped():
                print(
                    f"We have a connection which is already stopped in outBoundConnections. Connection.uid={connection.get_uid()}"
                )
                # Assuming 'out_bound_connections' is a global or class variable
                global out_bound_connections
                out_bound_connections.remove(connection)
                return None
            else:
                return connection
        else:
            return None

    @abstractmethod
    def get_socks5_proxy(self) -> Socks5Proxy:
        pass

    def get_all_connections(self):
        # Can contain inbound and outbound connections with the same peer node address,
        # as connection hashcode is using uid and port info
        connections = set(self.inbound_connections)
        connections.update(self.outbound_connections)
        return connections

    def get_confirmed_connections(self):
        # Can contain inbound and outbound connections with the same peer node address,
        # as connection hashcode is using uid and port info
        return {conn for conn in self.get_all_connections() if conn.peers_node_address}

    def get_node_address_of_confirmed_connections(self):
        # Does not contain inbound and outbound connection with the same peer node address
        return {conn.peers_node_address for conn in self.get_confirmed_connections()}

    def shut_down(self, shutdown_complete_handler: Optional[Callable] = None) -> None:
        logger.info("NetworkNode shutdown started")

        if not self.shutdown_in_progress:
            self.shutdown_in_progress = True

            if self.server:
                self.server.shut_down()
                self.server = None

            all_connections = self.get_all_connections()
            num_connections = len(all_connections)

            if num_connections == 0:
                logger.info("Shutdown immediately because no connections are open.")
                if shutdown_complete_handler:
                    shutdown_complete_handler()
                return

            logger.info(f"Shutdown {num_connections} connections")

            completed_count = threading.Lock()
            count = 0

            def timeout_handler():
                logger.info("Shutdown completed due timeout")
                if shutdown_complete_handler:
                    shutdown_complete_handler()

            timer: Timer = UserThread.run_after(
                timeout_handler, timedelta(milliseconds=1500)
            )

            def on_connection_shutdown(connection: "Connection"):
                nonlocal count
                with completed_count:
                    count += 1
                    logger.info(
                        f"Shutdown of node {connection.peers_node_address} completed"
                    )
                    if count == num_connections:
                        logger.info("Shutdown completed with all connections closed")
                        timer.stop()
                        self.connection_executor.shutdown(wait=False)
                        self.send_message_executor.shutdown(wait=False)
                        if shutdown_complete_handler:
                            shutdown_complete_handler()

            for connection in all_connections:
                connection.shut_down(
                    close_connection_reason=CloseConnectionReason.APP_SHUT_DOWN,
                    shutdown_complete_handler=lambda conn=connection: on_connection_shutdown(
                        conn
                    ),
                )

    ###########################################################################################
    ## SetupListener
    ###########################################################################################

    def add_setup_listener(self, setup_listener: "SetupListener"):
        self.setup_listeners.add(setup_listener)

    ###########################################################################################
    ## MessageListener implementation
    ###########################################################################################

    def on_message(self, network_envelope: "NetworkEnvelope", connection: "Connection"):
        for listener in self.message_listeners:
            listener.on_message(network_envelope, connection)

    ###########################################################################################
    ## Listeners
    ###########################################################################################

    def add_connection_listener(self, connection_listener):
        self.connection_listeners.add(connection_listener)

    def remove_connection_listener(self, connection_listener):
        self.connection_listeners.remove(connection_listener)

    def add_message_listener(self, message_listener):
        self.message_listeners.add(message_listener)

    def remove_message_listener(self, message_listener):
        self.message_listeners.remove(message_listener)

    ###########################################################################################
    ## Protected
    ###########################################################################################

    def start_server(self, server_socket: Socket):
        connection_listener = NetworkNodeServerConnectionListener(self)

        self.server = Server(
            server_socket=server_socket,
            message_listener=self,
            connection_listener=connection_listener,
            network_proto_resolver=self.network_proto_resolver,
            ban_filter=self.ban_filter,
        )
        self.server.start()

    @abstractmethod
    def createSocket(self, peers_node_address: NodeAddress) -> Socket:
        pass
    
    def find_peers_capabilities(self, node_address: NodeAddress) -> Optional["Capabilities"]:
        return next((connection.capabilities
                    for connection in self.get_confirmed_connections()
                    if connection.peers_node_address and connection.peers_node_address == node_address),
                    None)

    def up_time(self):
        """
        how long Bisq has been running with at least one connection in ms
        uptime is relative to last all connections lost event
        """
        earliest_connection = datetime.now().timestamp()
        for connection in self.outbound_connections:
            earliest_connection = min(earliest_connection, connection.statistic.creation_date.timestamp())
        return int((datetime.now().timestamp() - earliest_connection) * 1000)
    
    def get_inbound_connection_count(self):
        return len(self.inbound_connections)
    
    def get_outbound_connection_count(self):
        return len(self.outbound_connections)


class NetworkNodeOutboundConnectionListener(ConnectionListener):
    def __init__(self, network_node: "NetworkNode") -> None:
        self.network_node = network_node

    def on_connection(self, connection):
        if not connection.stopped:
            self.network_node.outbound_connections.add(connection)
            self.network_node.print_outbound_connections()
            for listener in self.network_node.connection_listeners:
                listener.on_connection(connection)

    def on_disconnect(self, close_connection_reason, connection):
        self.network_node.outbound_connections.remove(connection)
        self.network_node.print_outbound_connections()
        for listener in self.network_node.connection_listeners:
            listener.on_disconnect(close_connection_reason, connection)


class NetworkNodeServerConnectionListener(ConnectionListener):

    def __init__(self, network_node: "NetworkNode") -> None:
        super().__init__()
        self.network_node = network_node

    def on_connection(self, connection: "Connection"):
        if not connection.stopped:
            self.network_node.inbound_connections.add(connection)
            self.network_node.print_inbound_connections()
            for listener in self.network_node.connection_listeners:
                listener.on_connection(connection)

    def on_disconnect(
        self, close_connection_reason: "CloseConnectionReason", connection: "Connection"
    ):
        logger.debug(
            f"on_disconnect at server socket connectionListener\n\tconnection={connection}"
        )
        self.network_node.inbound_connections.remove(connection)
        self.network_node.print_inbound_connections()
        for listener in self.network_node.connection_listeners:
            listener.on_disconnect(close_connection_reason, connection)
