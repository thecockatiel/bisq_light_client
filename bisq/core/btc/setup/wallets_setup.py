from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from utils.data import SimpleProperty
from utils.dir import check_dir

if TYPE_CHECKING:
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.model.address_entry_list import AddressEntryList
    from bisq.common.config.config import Config
    from bisq.core.btc.setup.wallet_config import WalletConfig

logger = get_logger(__name__)


# TODO
class WalletsSetup:
    PRE_SEGWIT_BTC_WALLET_BACKUP = "pre_segwit_bisq_BTC.wallet.backup"
    PRE_SEGWIT_BSQ_WALLET_BACKUP = "pre_segwit_bisq_BSQ.wallet.backup"
    STARTUP_TIMEOUT_SEC = 180
    SPV_CHAIN_FILE_NAME = "bisq.spvchain"

    def __init__(
        self,
        address_entry_list: "AddressEntryList",
        preferences: "Preferences",
        socks5_proxy_provider: "Socks5ProxyProvider",
        config: "Config",
    ): 
        self._address_entry_list = address_entry_list
        self._preferences = preferences
        self._socks5_proxy_provider = socks5_proxy_provider
        self._config = config

        self.num_peers_property = SimpleProperty(0)
        self.download_percentage_property = SimpleProperty(100.0 / 100.0)
        self.chain_height_property = SimpleProperty(0)
        self.wallets_setup_failed_property = SimpleProperty(False)
        self.wallet_config: Optional["WalletConfig"] = None
        self.shut_down_complete_property = SimpleProperty(False)

    @property
    def params(self):
        return self._config.base_currency_network.parameters

    @property
    def is_download_complete(self):
        return True

    @property
    def has_sufficient_peers_for_broadcast(self):
        return True

    def is_chain_height_synced_within_tolerance(self):
        raise RuntimeError(
            "WalletsSetup.is_chain_height_synced_within_tolerance Not implemented yet"
        )

    def resync_spv_chain(self):
        self._config.wallet_dir.joinpath(WalletsSetup.SPV_CHAIN_FILE_NAME).unlink(
            missing_ok=True
        )

    def get_wallet_config(self):
        return self.wallet_config

    def shut_down(self):
        self.shut_down_complete_property.set(True)
        logger.info("wallets_setup.shut_down started")

        def on_shutdown_complete():
            logger.info("wallet_config shut down completed")
            self.shut_down_complete_property.set(True)

        if self.wallet_config:
            self.wallet_config.shut_down(on_shutdown_complete)
        else:
            on_shutdown_complete()
