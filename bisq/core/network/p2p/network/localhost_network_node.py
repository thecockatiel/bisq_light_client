from datetime import timedelta
from socket import socket as Socket
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.node_address import NodeAddress
import socket

if TYPE_CHECKING:
    from bisq.core.network.p2p.network.ban_filter import BanFilter
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.network.p2p.network.setup_listener import SetupListener

logger = get_logger(__name__)

class LocalhostNetworkNode(NetworkNode):
    simulate_tor_delay_tor_node = 500
    simulate_tor_delay_hidden_service = 500
    
    @staticmethod
    def set_simulate_tor_delay_tor_node(delay: int) -> None:
        LocalhostNetworkNode.simulate_tor_delay_tor_node = delay
    
    @staticmethod
    def set_simulate_tor_delay_hidden_service(delay: int) -> None:
        LocalhostNetworkNode.simulate_tor_delay_hidden_service = delay
    
    def __init__(self, service_port: int, network_proto_resolver: "NetworkProtoResolver", ban_filter: Optional["BanFilter"], max_connections: int):
        super().__init__(service_port, network_proto_resolver, ban_filter, max_connections)
        
    async def start(self, setup_listener: Optional["SetupListener"] = None):
        if setup_listener:
            self.add_setup_listener(setup_listener)
        
        
        def first():
            self.node_address_property.value = NodeAddress("localhost", self.service_port)
            
            for listener in self.setup_listeners:
                listener.on_tor_node_ready()
            
            # simulate tor HS publishing delay
            UserThread.run_after(second, timedelta(milliseconds=LocalhostNetworkNode.simulate_tor_delay_tor_node))
             
        def second():
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(('', self.service_port))
                server_socket.listen()
                self.start_server(server_socket)
            except Exception as e:
                logger.error("Exception at startServer: ", exc_info=e)

            for listener in self.setup_listeners:
                listener.on_hidden_service_published()
        
        # simulate tor connection delay
        UserThread.run_after(first, timedelta(milliseconds=LocalhostNetworkNode.simulate_tor_delay_hidden_service))
        
    # Called from NetworkNode thread
    def create_socket(self, peer_node_address: "NodeAddress") -> socket.socket:
        return socket.create_connection((peer_node_address.host_name, peer_node_address.port))