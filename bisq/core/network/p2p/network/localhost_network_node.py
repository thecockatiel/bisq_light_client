from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.timer import Timer
from utils.aio import as_future, get_asyncio_loop, wait_future_blocking
from collections.abc import Callable
from asyncio import Future
from electrum_min.util import wait_for2
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.node_address import NodeAddress
import socket
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from bisq.core.network.p2p.network.ban_filter import BanFilter
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.network.p2p.network.setup_listener import SetupListener


class LocalhostNetworkNode(NetworkNode):
    simulate_tor_delay_tor_node = 500
    simulate_tor_delay_hidden_service = 500
    
    @staticmethod
    def set_simulate_tor_delay_tor_node(delay: int) -> None:
        LocalhostNetworkNode.simulate_tor_delay_tor_node = delay
    
    @staticmethod
    def set_simulate_tor_delay_hidden_service(delay: int) -> None:
        LocalhostNetworkNode.simulate_tor_delay_hidden_service = delay
    
    def __init__(self, service_port: int, network_proto_resolver: "NetworkProtoResolver", ban_filter: Optional["BanFilter"], config: "Config"):
        super().__init__(service_port, network_proto_resolver, ban_filter, config)
        self.logger = get_ctx_logger(__name__)
        self.__create_socket_futures = ThreadSafeSet[Future]()
        self._server_timers = set[Timer]()
        
    async def start(self, setup_listener: Optional["SetupListener"] = None):
        if setup_listener:
            self.add_setup_listener(setup_listener)
        
        
        def first():
            self.node_address_property.value = NodeAddress("localhost", self.service_port)
            
            for listener in self.setup_listeners:
                listener.on_tor_node_ready()
            
            # simulate tor HS publishing delay
            self._server_timers.add(UserThread.run_after(second, timedelta(milliseconds=LocalhostNetworkNode.simulate_tor_delay_tor_node)))
             
        def second():
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(('', self.service_port))
                server_socket.listen()
                self.start_server(server_socket)
            except Exception as e:
                self.logger.error("Exception at startServer: ", exc_info=e)

            for listener in self.setup_listeners:
                listener.on_hidden_service_published()
        
        # simulate tor connection delay
        self._server_timers.add(UserThread.run_after(first, timedelta(milliseconds=LocalhostNetworkNode.simulate_tor_delay_hidden_service)))
        
    # Called from NetworkNode thread
    def create_socket(self, peer_node_address: "NodeAddress") -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        f = as_future(
            wait_for2(
                get_asyncio_loop().sock_connect(sock, (peer_node_address.host_name, peer_node_address.port)),
                240
            )
        )
        self.__create_socket_futures.add(f)
        try:
            wait_future_blocking(f)
        finally: 
            self.__create_socket_futures.discard(f)
            sock.setblocking(True)
        return sock
    
    def shut_down(self, shut_down_complete_handler: Optional[Callable[[], None]] = None):
        for timer in self._server_timers:
            timer.stop()
        self._server_timers.clear()
        if self.__create_socket_futures:
            for f in self.__create_socket_futures:
                f.cancel()
            self.__create_socket_futures.clear()
        return super().shut_down(shut_down_complete_handler)