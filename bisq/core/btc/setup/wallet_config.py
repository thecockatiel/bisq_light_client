import utils.aio  # importing it sets up stuff
from threading import Lock
from electrum_min.util import EventListener, event_listener
import asyncio
from pathlib import Path
from typing import Optional
from bitcoinj.wallet.wallet import Wallet
from electrum_min.wallet import (
    Abstract_Wallet,
    create_new_bisq_wallet,
)
from collections.abc import Callable
from bisq.common.setup.log_setup import get_logger
from electrum_min.daemon import Daemon
from electrum_min.simple_config import SimpleConfig
from bisq.common.config.config import Config
from utils.data import SimpleProperty
from utils.preconditions import check_state


logger = get_logger(__name__)


# TODO
class WalletConfig(EventListener):
    """
    Tries to do the same thing as WalletConfig in bisq, except with electrum as it's wallet

    It basically sets up electrum to be used in bisq client
    """

    BTC_SEGWIT_PATH = "m/44'/0'/1'"
    BSQ_SEGWIT_PATH = "m/44'/142'/1'"
    BSQ_WALLET_FILE_NAME = "bisq_BSQ.wallet"
    BTC_WALLET_FILE_NAME = "bisq_BTC.wallet"

    def __init__(self, config: "Config", seed: Optional[str] = None):
        self._config = config

        self._daemon: Optional["Daemon"] = None
        self._btc_wallet: Optional["Wallet"] = None
        self._bsq_wallet: Optional["Wallet"] = None
        self._initializing = False
        self._initialized = False
        self._restore_from_seed: Optional[str] = seed
        self._lock = Lock()
        self._current_height_property = SimpleProperty(0)
        self._num_peers_property = SimpleProperty(0)

    @property
    def is_ready(self):
        return self._initialized

    @property
    def btc_wallet(self):
        check_state(self.is_ready, "Cannot call until startup is complete")
        return self._btc_wallet

    @property
    def bsq_wallet(self):
        check_state(self.is_ready, "Cannot call until startup is complete")
        return self._bsq_wallet

    @property
    def current_height_property(self):
        return self._current_height_property

    @property
    def num_peers_property(self):
        return self._num_peers_property

    @event_listener
    def on_event_blockchain_updated(self):
        self._current_height_property.value = self._daemon.network.get_local_height()

    @event_listener
    def on_event_network_updated(self):
        self._num_peers_property.value = len(self._daemon.network.get_interfaces())

    def start_up(
        self,
        on_complete: Callable[[], None],
        exception_handler: Callable[[Exception], None],
    ):
        with self._lock:
            if self._initializing or self._initialized:
                raise RuntimeError("Already starting up or already started up")
            self._initializing = True
            options = {}
            try:
                EventListener.register_callbacks(self)
                if self._config.base_currency_network.is_testnet():
                    options["testnet"] = True
                elif (
                    self._config.base_currency_network.is_regtest()
                    or self._config.base_currency_network.is_dao_testnet()
                    or self._config.base_currency_network.is_dao_regtest()
                ):
                    options["regtest"] = True
                self._electrum_config = SimpleConfig(
                    options=options,
                    read_user_dir_function=lambda: str(self._config.wallet_dir),
                )
                if self._config.tor_control_host:
                    self._electrum_config.NETWORK_PROXY = (
                        self._config.tor_control_host
                        + ":"
                        + str(self._config.tor_control_port)
                    )
                if self._config.tor_proxy_username:
                    self._electrum_config.NETWORK_PROXY_USER = (
                        self._config.tor_proxy_username
                    )
                if self._config.tor_proxy_password:
                    self._electrum_config.NETWORK_PROXY_PASSWORD = (
                        self._config.tor_proxy_password
                    )

                self._daemon = Daemon(
                    self._electrum_config,
                    listen_jsonrpc=False,
                    start_network=False,
                )

                btc_wallet_file = self._config.wallet_dir.joinpath(
                    WalletConfig.BTC_WALLET_FILE_NAME
                )

                bsq_wallet_file = self._config.wallet_dir.joinpath(
                    WalletConfig.BSQ_WALLET_FILE_NAME
                )
                # TODO: define and use password
                self._btc_wallet = Wallet(
                    self._create_or_load_wallet(
                        # TODO: check should_replay_wallet later to see if needed
                        bool(self._restore_from_seed),
                        btc_wallet_file,
                        False,
                    ),
                    self._config.network_parameters,
                )
                self._bsq_wallet = Wallet(
                    self._create_or_load_wallet(
                        # TODO: check should_replay_wallet later to see if needed
                        bool(self._restore_from_seed),
                        bsq_wallet_file,
                        False,
                    ),
                    self._config.network_parameters,
                )
                self._restore_from_seed = None
                self._daemon.start_network()
                self._btc_wallet.start_network(self._daemon.network)
                self._bsq_wallet.start_network(self._daemon.network)
                self._initializing = False
                self._initialized = True
                on_complete()
            except Exception as e:
                exception_handler(e)

    def shut_down(self, complete_handler: Callable[[], None]):
        with self._lock:
            EventListener.unregister_callbacks(self)
            if self._daemon is None:
                self._initialized = False
                complete_handler()
            else:
                btc_stop_task = asyncio.create_task(self._btc_wallet.stop())
                bsq_stop_task = asyncio.create_task(self._bsq_wallet.stop())

                async def stop_wallets_and_daemon():
                    await asyncio.gather(btc_stop_task, bsq_stop_task)
                    await self._daemon.stop()
                    self._initialized = False
                    complete_handler()

                asyncio.create_task(stop_wallets_and_daemon())

    def _create_or_load_wallet(
        self,
        should_replay_wallet: bool,
        wallet_file: Path,
        is_bsq_wallet: bool,
    ):
        self._maybe_move_old_wallet_out_of_the_way(wallet_file)

        if wallet_file.exists():
            wallet = self._load_wallet(should_replay_wallet, wallet_file)
        else:
            wallet = self._create_wallet(wallet_file, is_bsq_wallet)
            self._daemon.add_wallet(wallet)

        return wallet

    # TODO: later wait for password before initializing the app
    def _load_wallet(
        self,
        should_replay_wallet: bool,
        wallet_file: Path,
        password=None,
    ):
        wallet = self._daemon.load_wallet(str(wallet_file.resolve()), password=password)
        if should_replay_wallet:
            wallet.clear_history()
        return wallet

    def _create_wallet(self, path: Path, is_bsq_wallet: bool) -> "Abstract_Wallet":
        if is_bsq_wallet:
            result = create_new_bisq_wallet(
                path=str(path),
                config=self._electrum_config,
                derivation_path=WalletConfig.BSQ_SEGWIT_PATH,
                encrypt_file=False,
                # here, "None" is password. gets the seed from the btc wallet we created a moment ago
                seed=self._restore_from_seed
                or self._btc_wallet.keystore.get_seed(None),
            )
            return result["wallet"]
        else:
            result = create_new_bisq_wallet(
                path=str(path),
                config=self._electrum_config,
                derivation_path=WalletConfig.BTC_SEGWIT_PATH,
                encrypt_file=False,
                seed=self._restore_from_seed,
            )
            return result["wallet"]

    def _maybe_move_old_wallet_out_of_the_way(self, wallet_file: Path):
        if not self._restore_from_seed:
            return
        if not wallet_file.exists():
            return

        counter = 1
        parent = wallet_file.parent
        while True:
            new_name = parent.joinpath(f"Backup {counter} for {wallet_file.name}")
            counter += 1
            if not new_name.exists():
                break

        logger.info(f"Renaming old wallet file {wallet_file} to {new_name}")
        try:
            wallet_file.rename(new_name)
        except Exception as e:
            # This should not happen unless something is really messed up
            raise RuntimeError(f"Failed to rename wallet for restore: {e}")
