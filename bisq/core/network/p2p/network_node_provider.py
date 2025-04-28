from pathlib import Path
from typing import TYPE_CHECKING, Optional

from bisq.common.config.config import Config
from bisq.core.network.p2p.network.limited_running_tor import LimitedRunningTor
from bisq.core.network.p2p.network.localhost_network_node import LocalhostNetworkNode
from bisq.core.network.p2p.network.network_node import NetworkNode
from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.core.network.p2p.network.running_tor import RunningTor
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.network.p2p.network.tor_mode import TorMode

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.network.p2p.network.bridge_address_provider import (
        BridgeAddressProvider,
    )
    from bisq.core.network.p2p.network.ban_filter import BanFilter


class NetworkNodeProvider:
    def __init__(
        self,
        network_proto_resolver: "NetworkProtoResolver",
        bridge_address_provider: "BridgeAddressProvider",
        ban_filter: Optional["BanFilter"],
        config: "Config",
        tor_dir: Path,
    ):
        self.tor_dir = tor_dir
        if config.use_localhost_for_p2p:
            self.network_node = LocalhostNetworkNode(
                config.node_port,
                network_proto_resolver,
                ban_filter,
                config,
            )
        else:
            tor_mode = self._get_tor_mode(
                bridge_address_provider,
                config,
            )
            self.network_node = TorNetworkNode(
                config.node_port,
                network_proto_resolver,
                tor_mode,
                ban_filter,
                config,
            )

    def _get_tor_mode(
        self, bridge_address_provider: "BridgeAddressProvider", config: "Config"
    ) -> TorMode:
        if config.tor_control_port != Config.UNSPECIFIED_PORT:
            return RunningTor(
                self.tor_dir,
                config.tor_control_host,
                config.tor_control_port,
                config.tor_control_password,
            )

        if config.tor_proxy_port != Config.UNSPECIFIED_PORT:
            return LimitedRunningTor(
                config.tor_proxy_host,
                config.tor_proxy_port,
                config.tor_proxy_hidden_service_name,
                config.tor_proxy_hidden_service_port,
                config.tor_proxy_hidden_service_target_port,
                config.tor_proxy_username,
                config.tor_proxy_password,
            )

        return NewTor(
            config.app_data_dir,
            self.tor_dir,
            config.torrc_file,
            config.torrc_options,
            bridge_address_provider,
            config.tor_use_bridges_file,
        )

    def get(self) -> NetworkNode:
        return self.network_node
