from typing import TYPE_CHECKING, Optional
from collections.abc import Callable
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import socks
import socket

from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.network.hidden_service_socket import HiddenServiceSocket
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.setup_listener import SetupListener
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.utils.utils import Utils
from utils.aio import run_in_thread
from utils.time import get_time_ms
from bisq.core.network.p2p.node_address import NodeAddress

if TYPE_CHECKING:
    from txtorcon import Tor
    from bisq.core.network.p2p.network.tor_mode import TorMode
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
    from bisq.common.timer import Timer
    from bisq.core.network.p2p.network.ban_filter import BanFilter
    
logger = get_logger(__name__)

# NOTE: removed experimental stream isolation
# NOTE: the setup used here finishes for new tor instance and publishing hidden service at the same time. unlike java version which does it in two steps.
class TorNetworkNode(NetworkNode):
    SHUT_DOWN_TIMEOUT_SEC = 2

    def __init__(
        self,
        service_port: int,
        network_proto_resolver: "NetworkProtoResolver",
        tor_mode: "TorMode",
        ban_filter: Optional["BanFilter"],
        max_connections: int,
    ):
        super().__init__(
            service_port, network_proto_resolver, ban_filter, max_connections
        )

        self.hidden_service_socket: "HiddenServiceSocket" = None
        self.shut_down_timeout_timer: "Timer" = None
        self.tor: Optional["Tor"] = None
        self.tor_mode = tor_mode
        self.socks_proxy: Optional["Socks5Proxy"] = None
        self.shut_down_in_progress = False
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="StartTor")

    async def start(self, setup_listener: Optional["SetupListener"] = None):
        await run_in_thread(self.tor_mode.do_rolling_backup)
        
        if setup_listener:
            self.add_setup_listener(setup_listener)

        await self.create_tor_and_hidden_service(Utils.find_free_system_port(), self.service_port)
        
    def create_socket(self, peer_node_address: "NodeAddress") -> socket.socket:
        assert peer_node_address.host_name.endswith(".onion"), "PeerAddress is not an onion address"
        assert self.tor, "Tor instance not ready"
        assert self.tor._config, "Tor config not ready"
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(240) # Connection.SOCKET_TIMEOUT_SEC
        sock.set_proxy(
            proxy_type=socks.SOCKS5,
            addr="127.0.0.1",
            port=int(self.tor._config.SOCKSPort[0]),
            rdns=True,
        )
        sock.connect((peer_node_address.host_name, peer_node_address.port))
        return sock
    
    def get_socks_proxy(self) -> Socks5Proxy:
        if not self.socks_proxy:
            assert self.tor, "Tor instance not ready at get_socks_proxy"
            assert self.tor._config, "Tor config not ready at get_socks_proxy"
            self.socks_proxy = Socks5Proxy("127.0.0.1", self.tor._config.SOCKSPort)
        return self.socks_proxy

    def shut_down(self, shut_down_complete_handler: Optional[Callable[[], None]] = None):
        logger.info("TorNetworkNode shutdown started")
        if self.shut_down_in_progress:
            logger.warning("We got shutDown already called")
            return
        
        self.shut_down_in_progress = True

        def timeout_handler():
            logger.error("A timeout occurred at shutDown")
            if shut_down_complete_handler:
                shut_down_complete_handler()
            self.executor.shutdown(wait=False)

        self.shut_down_timeout_timer = UserThread.run_after(
            timeout_handler, 
            timedelta(seconds=TorNetworkNode.SHUT_DOWN_TIMEOUT_SEC)
        )

        def complete_handler():
            try:
                if self.tor:
                    self.tor.quit() # NOTE: we didn't wait for the tor to quit
                    self.tor = None
                    logger.info("Tor shutdown completed")
                self.executor.shutdown(wait=False)
            except Exception as e:
                logger.error("Shutdown torNetworkNode failed with exception", exc_info=e)
            finally:
                if self.shut_down_timeout_timer:
                    self.shut_down_timeout_timer.stop()
                if shut_down_complete_handler:
                    shut_down_complete_handler()

        super().shut_down(complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Create tor and hidden service
    # ///////////////////////////////////////////////////////////////////////////////////////////
    async def create_tor_and_hidden_service(self, local_port: int, service_port: int):
        ts = get_time_ms()
        try:
            self.tor = await self.tor_mode.get_tor()
            
            def call_listeners():
                for listener in self.setup_listeners:
                    listener.on_tor_node_ready()
                    
            UserThread.execute(call_listeners)
            
            self.hidden_service_socket = HiddenServiceSocket(local_port, str(self.tor_mode.get_hidden_service_directory()), service_port, self)
            
            await self.hidden_service_socket.initialize()
            
            node_address = NodeAddress.from_full_address(f"{self.hidden_service_socket.service_name}:{self.hidden_service_socket.hidden_service_port}")
            self.node_address_property.set(node_address)
            
            logger.info(
                "\n################################################################\n"
                f"Tor hidden service published after {get_time_ms() - ts} ms. Socket={self.hidden_service_socket}\n"
                "################################################################"
            )
            
            def start():
                self.start_server(self.hidden_service_socket.server_socket)
                for listener in self.setup_listeners:
                    listener.on_hidden_service_published()
            
            UserThread.execute(start)

        except Exception as e:
            logger.error(f"Starting tor node failed: {e}", exc_info=e)
            if isinstance(e.__cause__, IOError):
                def notify_failure():
                    for listener in self.setup_listeners:
                        listener.on_setup_failed(RuntimeError(str(e)))
                UserThread.execute(notify_failure)
            else:
                def request_bridges():
                    for listener in self.setup_listeners:
                        listener.on_request_custom_bridges()
                UserThread.execute(request_bridges)
                logger.warning("We shutdown as starting tor with the default bridges failed. We request user to add custom bridges.")
                self.shut_down()