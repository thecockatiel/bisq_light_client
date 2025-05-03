from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from utils.data import SimpleProperty, combine_simple_properties

if TYPE_CHECKING:
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.network.p2p.p2p_service import P2PService


class AppStartupState:

    def __init__(
        self,
        wallets_setup: "WalletsSetup",
        p2p_service: "P2PService",
    ):
        self.p2p_network_and_wallet_initialized = SimpleProperty(False)
        self.wallet_synced = SimpleProperty(False)
        self.all_domain_services_initialized = SimpleProperty(False)
        self.application_fully_initialized = SimpleProperty(False)
        self.data_received = SimpleProperty(False)
        self.has_sufficient_peers_for_broadcast = SimpleProperty(False)
        self._subscriptions: list[Callable[[], None]] = []

        class P2PListener(BootstrapListener):
            def on_data_received(self_):
                self.data_received.set(True)

        self._subscriptions.append(p2p_service.add_p2p_service_listener(P2PListener()))

        def on_wallets_setup_completed(e):
            if wallets_setup.is_download_complete:
                self.wallet_synced.set(True)
                wallets_setup.chain_height_property.remove_listener(
                    on_wallets_setup_completed
                )

        self._subscriptions.append(
            wallets_setup.chain_height_property.add_listener(on_wallets_setup_completed)
        )

        self._subscriptions.append(
            wallets_setup.num_peers_property.add_listener(
                lambda _: (
                    self.has_sufficient_peers_for_broadcast.set(True)
                    if wallets_setup.has_sufficient_peers_for_broadcast
                    else None
                )
            )
        )

        self.p2p_network_and_wallet_initialized = combine_simple_properties(
            self.data_received,
            self.wallet_synced,
            self.has_sufficient_peers_for_broadcast,
            self.all_domain_services_initialized,
            transform=all,
        )

        self._subscriptions.append(
            self.p2p_network_and_wallet_initialized.add_listener(
                lambda e: (
                    self.application_fully_initialized.set(True)
                    if e.new_value
                    else None
                )
            )
        )

    def on_domain_services_initialized(self):
        self.all_domain_services_initialized.set(True)

    def shut_down(self):
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()
        self.p2p_network_and_wallet_initialized = None