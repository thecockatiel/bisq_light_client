from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.file.file_util import (
    delete_directory,
    rolling_backup,
)
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from utils.data import SimpleProperty, SimplePropertyChangeEvent
from bisq.core.btc.setup.wallet_config import WalletConfig

if TYPE_CHECKING:
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.model.address_entry_list import AddressEntryList
    from bisq.common.config.config import Config

logger = get_logger(__name__)


# TODO
class WalletsSetup:
    STARTUP_TIMEOUT_SEC = 180
    SPV_CHAIN_FILE_NAME = "blockchain_headers"

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

        self._chain_height_property = SimpleProperty(0)
        self._num_peers_property = SimpleProperty(0)
        self._setup_completed_handlers: set[Callable[[], None]] = set()

        self.wallets_setup_failed_property = SimpleProperty(False)
        self.wallet_config: Optional["WalletConfig"] = None
        self.shut_down_complete_property = SimpleProperty(False)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lifecycle
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def initialize(
        self,
        seed: Optional[str],
        result_handler: ResultHandler,
        exception_handler: Callable[[Exception], None],
    ):
        timeout_timer = UserThread.run_after(
            lambda: exception_handler(
                TimeoutError(
                    f"Wallet did not initialize in {WalletsSetup.STARTUP_TIMEOUT_SEC} seconds."
                )
            ),
            timedelta(
                seconds=WalletsSetup.STARTUP_TIMEOUT_SEC,
            ),
        )
        self.backup_wallets()

        self.wallet_config = WalletConfig(self._config, seed)
        self.wallet_config.current_height_property.add_listener(self._new_chain_height)
        self.wallet_config.num_peers_property.add_listener(self._new_peer_count)

        def on_complete():
            timeout_timer.stop()
            self._chain_height_property.set(self.wallet_config.current_height_property.value)
            UserThread.execute(
                lambda: (
                    self._address_entry_list.on_wallet_ready(
                        self.wallet_config.btc_wallet
                    ),
                    [handler() for handler in self._setup_completed_handlers],
                )
            )
            UserThread.run_after(
                result_handler,
                timedelta(milliseconds=100),
            )

        def on_exception(e: Exception):
            timeout_timer.stop()
            self.wallet_config = None
            logger.error("WalletsSetup.initialize failed", exc_info=e)
            self.wallets_setup_failed_property.set(True)
            UserThread.execute(lambda: exception_handler(e))

        self.wallet_config.start_up(on_complete, on_exception)

    def resync_spv_chain(self):
        self._config.wallet_dir.joinpath(WalletsSetup.SPV_CHAIN_FILE_NAME).unlink(
            missing_ok=True
        )

    def shut_down(self):
        self.shut_down_complete_property.set(True)
        logger.info("wallets_setup.shut_down started")

        def on_shutdown_complete():
            logger.info("wallet_config shut down completed")
            self.shut_down_complete_property.set(True)

        if self.wallet_config:
            self.wallet_config.current_height_property.remove_listener(
                self._new_chain_height
            )
            self.wallet_config.num_peers_property.remove_listener(self._new_peer_count)
            self.wallet_config.shut_down(on_shutdown_complete)
        else:
            on_shutdown_complete()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Backup
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def backup_wallets(self):
        rolling_backup(
            self._config.wallet_dir,
            WalletConfig.BTC_WALLET_FILE_NAME,
            20,
        )
        rolling_backup(
            self._config.wallet_dir,
            WalletConfig.BSQ_WALLET_FILE_NAME,
            20,
        )

    def clear_backups(self):
        # we dont touch pre segwit stuff in python client
        try:
            delete_directory(self._config.wallet_dir.joinpath("backup"))
        except Exception as e:
            logger.error(f"Could not delete directory: {e}", exc_info=e)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Restore
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def restore_seed_words(
        self,
        seed: Optional[str],
        result_handler: ResultHandler,
        exception_handler: Callable[[Exception], None],
    ):
        assert bool(seed), "Seed must be present at restore_seed_words"
        self.backup_wallets()

        def on_shutdown_complete():
            self.initialize(seed, result_handler, exception_handler)

        self.wallet_config.shut_down(on_shutdown_complete)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Handlers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_setup_completed_handler(self, handler: Callable[[], None]):
        self._setup_completed_handlers.add(handler)

    def remove_setup_completed_handler(self, handler: Callable[[], None]):
        self._setup_completed_handlers.discard(handler)

    def _new_peer_count(self, e: SimplePropertyChangeEvent[int]):
        self._num_peers_property.set(e.new_value)

    def _new_chain_height(self, e: SimplePropertyChangeEvent[int]):
        self._chain_height_property.set(e.new_value)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def params(self):
        return self._config.base_currency_network.parameters

    @property
    def is_download_complete(self):
        return self._chain_height_property.value > 0

    @property
    def has_sufficient_peers_for_broadcast(self):
        return self._num_peers_property.value > 0

    @property
    def chain_height_property(self):
        return self._chain_height_property

    @property
    def num_peers_property(self):
        return self._num_peers_property

    @property
    def btc_wallet(self):
        return self.wallet_config.btc_wallet

    @property
    def bsq_wallet(self):
        return self.wallet_config.bsq_wallet

    @property
    def is_chain_height_synced_within_tolerance(self):
        # since we use electrum, we only need to know if its initialized or not
        if not self.wallet_config:
            return False

        return self.wallet_config.current_height_property.value > 0

    def get_addresses_by_context(self, context: "AddressEntryContext"):
        return {
            address_entry.get_address()
            for address_entry in self._address_entry_list.entry_set.copy()
            if address_entry.context == context
        }