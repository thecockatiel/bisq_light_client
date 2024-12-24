from typing import TYPE_CHECKING, Optional
from pathlib import Path

from bisq.common.config.config import Config
from bisq.core.network.p2p.network.localhost_network_node import LocalhostNetworkNode
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.core.network.p2p.network.running_tor import RunningTor
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.network.p2p.network.tor_mode import TorMode

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.network.p2p.network.bridge_address_provider import BridgeAddressProvider
    from bisq.core.network.p2p.network.ban_filter import BanFilter

class NetworkNodeProvider:
    def __init__(self,
                 network_proto_resolver: "NetworkProtoResolver",
                 bridge_address_provider: "BridgeAddressProvider",
                 ban_filter: Optional["BanFilter"],
                 max_connections: int,
                 use_localhost_for_p2p: bool,
                 port: int,
                 app_data_dir: Path,
                 tor_dir: Path,
                 torrc_file: Optional[Path],
                 torrc_options: str,
                 control_host: str,
                 control_port: int,
                 password: str,
                 use_bridges_file: bool):
        
        if use_localhost_for_p2p:
            self.network_node = LocalhostNetworkNode(port, network_proto_resolver, ban_filter, max_connections)
        else:
            tor_mode = self._get_tor_mode(
                bridge_address_provider,
                app_data_dir,
                tor_dir,
                torrc_file,
                torrc_options,
                control_host,
                control_port,
                password,
                use_bridges_file,
            )
            self.network_node = TorNetworkNode(port, network_proto_resolver, 
                                             tor_mode, ban_filter, max_connections)

    def _get_tor_mode(self,
                      bridge_address_provider: "BridgeAddressProvider",
                      app_data_dir: Path,
                      tor_dir: Path,
                      torrc_file: Optional[Path],
                      torrc_options: str,
                      control_host: str,
                      control_port: int,
                      password: str,
                      use_bridges_file: bool) -> TorMode:
        if control_port != Config.UNSPECIFIED_PORT:
            return RunningTor(tor_dir, control_host, control_port, password)
            
        return NewTor(app_data_dir, tor_dir, torrc_file, torrc_options, bridge_address_provider, use_bridges_file)

    def get(self) -> NetworkNode:
        return self.network_node