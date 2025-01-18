from aiohttp_socks import open_connection, ProxyType
from utils.aio import as_future, run_in_thread
from asyncio import Future, StreamReader, StreamWriter
from bisq.core.network.p2p.network.limited_running_tor import LimitedRunningTor
from electrum_min.util import wait_for2
from typing import TYPE_CHECKING, Optional
from collections.abc import Callable
from datetime import timedelta

from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.network.hidden_service_socket import HiddenServiceSocket
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.network.setup_listener import SetupListener
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.utils.utils import Utils
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
        
        if isinstance(tor_mode, LimitedRunningTor):
            self.service_port = tor_mode.hiddenservice_port
            self._socks_proxy = Socks5Proxy(tor_mode.proxy_host, tor_mode.proxy_port, tor_mode.proxy_username, tor_mode.proxy_password)
        else:
            self._socks_proxy: Optional["Socks5Proxy"] = None
        
        self.hidden_service_socket: "HiddenServiceSocket" = None
        self.shut_down_timeout_timer: "Timer" = None
        self.tor: Optional["Tor"] = None
        self.tor_mode = tor_mode
        self.__shutdown_in_progress = False

    async def start(self, setup_listener: Optional["SetupListener"] = None):
        await run_in_thread(self.tor_mode.do_rolling_backup)
        
        if setup_listener:
            self.add_setup_listener(setup_listener)

        if isinstance(self.tor_mode, LimitedRunningTor):
            local_port = self.tor_mode.hiddenservice_target_port
        else: 
            local_port = Utils.find_free_system_port()
        await self.create_tor_and_hidden_service(local_port, self.service_port)
        
    async def create_socket(self, peer_node_address: "NodeAddress") -> tuple[StreamReader, StreamWriter]:
        assert peer_node_address.host_name.endswith(".onion"), "PeerAddress is not an onion address"
        assert self.socks_proxy, "Tor proxy not ready"
        stream_tuple = await wait_for2(
            open_connection(
                host=peer_node_address.host_name,
                port=peer_node_address.port,
                proxy_type=ProxyType.SOCKS5,
                proxy_host="127.0.0.1",
                proxy_port=self.socks_proxy.port,
                rdns=True,
                username=self.socks_proxy.username,
                password=self.socks_proxy.password,
            ),
            240,  # Connection.SOCKET_TIMEOUT_SEC
        )
        return stream_tuple
    
    @property
    def socks_proxy(self) -> Socks5Proxy:
        if not self._socks_proxy:
            assert self.tor, "Tor instance not ready at get_socks_proxy"
            assert self.tor._config, "Tor config not ready at get_socks_proxy"
            self._socks_proxy = Socks5Proxy("127.0.0.1", int(self.tor._config.SOCKSPort[0]))
        return self._socks_proxy
    
    def get_socks_proxy(self) -> Socks5Proxy:
        return self.socks_proxy

    def shut_down(self, shut_down_complete_handler: Optional[Callable[[], None]] = None):
        logger.info(f"TorNetworkNode shutdown started at {get_time_ms()}")
        if self.__shutdown_in_progress:
            logger.warning("We got shutDown already called")
            return
        
        self.__shutdown_in_progress = True

        def timeout_handler():
            logger.error(f"A timeout occurred at shutDown at {get_time_ms()}")
            if shut_down_complete_handler:
                shut_down_complete_handler()

        self.shut_down_timeout_timer = UserThread.run_after(
            timeout_handler, 
            timedelta(seconds=TorNetworkNode.SHUT_DOWN_TIMEOUT_SEC)
        )

        def complete_handler():
            try:
                if self.tor:
                    as_future(self.tor.quit()) # NOTE: we didn't wait for the tor to quit
                    self.tor = None
                    logger.info(f"Tor shutdown completed at {get_time_ms()}")
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
            
            self.hidden_service_socket = HiddenServiceSocket(local_port, self.tor_mode.get_hidden_service_directory(), service_port, self.tor)
            
            await self.hidden_service_socket.initialize()
            
            if isinstance(self.tor_mode, LimitedRunningTor):
                self.hidden_service_socket._onion_hostname = self.tor_mode.hiddenservice_hostname
            
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
            if isinstance(e.__cause__, IOError) or "Trying to add hidden service" in str(e):
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
