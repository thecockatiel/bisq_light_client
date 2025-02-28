from asyncio import Future
from collections.abc import Callable
from datetime import timedelta
import random
from typing import TYPE_CHECKING, Optional
import shutil
from bisq.common.app.dev_env import DevEnv
from bisq.common.config.base_currency_network import BaseCurrencyNetwork
from bisq.common.file.file_util import get_usable_space
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.common.util.utilities import is_qubes_os
from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.app.bisq_setup_listener import BisqSetupListener
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.locale.res import Res
from bisq.core.network.utils.utils import Utils
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.trade.bisq_v1.trade_tx_exception import TradeTxException
from bisq.core.util.coin.coin_formatter import CoinFormatter
from bisq.core.util.formatting_util import FormattingUtils
from utils.aio import as_future, run_in_thread
from utils.data import (
    SimpleProperty,
    SimplePropertyChangeEvent,
    combine_simple_properties,
)
from bisq.core.btc.wallet.http.mem_pool_space_tx_broadcaster import (
    MemPoolSpaceTxBroadcaster,
)
from bisq.common.version import Version
from bisq.core.account.witness.account_age_witness_service import (
    AccountAgeWitnessService,
)

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
        PersistableNetworkPayload,
    )
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.payment.amazon_gift_card_account import AmazonGiftCardAccount
    from bisq.core.payment.revolute_account import RevolutAccount
    from bisq.common.app.p2p_network_setup import P2PNetworkSetup
    from bisq.common.config.config import Config
    from bisq.core.account.sign.signed_witness_storage_service import (
        SignedWitnessStorageService,
    )
    from bisq.core.alert.alert import Alert
    from bisq.core.alert.alert_manager import AlertManager
    from bisq.core.alert.private_notification_manager import PrivateNotificationManager
    from bisq.core.alert.private_notification_payload import PrivateNotificationPayload
    from bisq.core.app.app_startup_state import AppStartupState
    from bisq.core.app.domain_initialisation import DomainInitialisation
    from bisq.core.app.wallet_app_setup import WalletAppSetup
    from bisq.core.btc.nodes.local_bitcoin_node import LocalBitcoinNode
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bisq.core.dao.governance.voteresult.vote_result_exception import (
        VoteResultException,
    )
    from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list_service import (
        UnconfirmedBsqChangeOutputListService,
    )
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.support.dispute.arbitration.arbitration_manager import (
        ArbitrationManager,
    )
    from bisq.core.support.dispute.mediation.mediation_manager import MediationManager
    from bisq.core.support.refund.refund_manager import RefundManager
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.user.preferences import Preferences
    from bisq.core.user.user import User


logger = get_logger(__name__)


# NOTE: I know that IO is blocking, but since this is setup, I think it will be fine and it will reduce the complexity of making them async
# TODO: dependencies must be implemented before this is usable. (Wallets functionality must be present)
class BisqSetup:
    VERSION_FILE_NAME = "version"
    RESYNC_SPV_FILE_NAME = "resyncSpv"
    STARTUP_TIMEOUT_MINUTES = 4

    def __init__(
        self,
        domain_initialisation: "DomainInitialisation",
        p2p_network_setup: "P2PNetworkSetup",
        wallet_app_setup: "WalletAppSetup",
        wallets_manager: "WalletsManager",
        wallets_setup: "WalletsSetup",
        btc_wallet_service: "BtcWalletService",
        p2p_service: "P2PService",
        private_notification_manager: "PrivateNotificationManager",
        signed_witness_storage_service: "SignedWitnessStorageService",
        trade_manager: "TradeManager",
        open_offer_manager: "OpenOfferManager",
        preferences: "Preferences",
        user: "User",
        alert_manager: "AlertManager",
        unconfirmed_bsq_change_output_list_service: "UnconfirmedBsqChangeOutputListService",
        config: "Config",
        account_age_witness_service: "AccountAgeWitnessService",
        formatter: "CoinFormatter",  # FormattingUtils.BTC_FORMATTER_KEY
        local_bitcoin_node: "LocalBitcoinNode",
        app_startup_state: "AppStartupState",
        socks5_proxy_provider: "Socks5ProxyProvider",
        mediation_manager: "MediationManager",
        refund_manager: "RefundManager",
        arbitration_manager: "ArbitrationManager",
    ):
        self.domain_initialisation: "DomainInitialisation" = domain_initialisation
        self.p2p_network_setup: "P2PNetworkSetup" = p2p_network_setup
        self.wallet_app_setup: "WalletAppSetup" = wallet_app_setup
        self.wallets_manager: "WalletsManager" = wallets_manager
        self.wallets_setup: "WalletsSetup" = wallets_setup
        self.btc_wallet_service: "BtcWalletService" = btc_wallet_service
        self.p2p_service: "P2PService" = p2p_service
        self.private_notification_manager: "PrivateNotificationManager" = (
            private_notification_manager
        )
        self.signed_witness_storage_service: "SignedWitnessStorageService" = (
            signed_witness_storage_service
        )
        self.trade_manager: "TradeManager" = trade_manager
        self.open_offer_manager: "OpenOfferManager" = open_offer_manager
        self.preferences: "Preferences" = preferences
        self.user: "User" = user
        self.alert_manager: "AlertManager" = alert_manager
        self.unconfirmed_bsq_change_output_list_service: (
            "UnconfirmedBsqChangeOutputListService"
        ) = unconfirmed_bsq_change_output_list_service
        self.config: "Config" = config
        self.account_age_witness_service: "AccountAgeWitnessService" = (
            account_age_witness_service
        )
        self.formatter: "CoinFormatter" = formatter
        self.local_bitcoin_node: "LocalBitcoinNode" = local_bitcoin_node
        self.app_startup_state: "AppStartupState" = app_startup_state
        self.mediation_manager: "MediationManager" = mediation_manager
        self.refund_manager: "RefundManager" = refund_manager
        self.arbitration_manager: "ArbitrationManager" = arbitration_manager
        # ---------------------------
        # ---------------------------
        self.display_tac_handler: Optional[Callable[[Callable[[], None]], None]] = None
        self.chain_file_locked_exception_handler: Optional[Callable[[str], None]] = None
        self.spv_file_corrupted_handler: Optional[Callable[[str], None]] = None
        self.locked_up_funds_handler: Optional[Callable[[str], None]] = None
        self.dao_error_message_handler: Optional[Callable[[str], None]] = None
        self.dao_warn_message_handler: Optional[Callable[[str], None]] = None
        self.filter_warning_handler: Optional[Callable[[str], None]] = None
        self.display_security_recommendation_handler: Optional[
            Callable[[str], None]
        ] = None
        self.display_localhost_handler: Optional[Callable[[str], None]] = None
        self.wrong_os_architecture_handler: Optional[Callable[[str], None]] = None
        self.display_signed_by_arbitrator_handler: Optional[Callable[[str], None]] = (
            None
        )
        self.display_signed_by_peer_handler: Optional[Callable[[str], None]] = None
        self.display_peer_limit_lifted_handler: Optional[Callable[[str], None]] = None
        self.display_peer_signer_handler: Optional[Callable[[str], None]] = None
        self.rejected_tx_error_message_handler: Optional[Callable[[str], None]] = None
        self.disk_space_warning_handler: Optional[Callable[[str], None]] = None
        self.offer_disabled_handler: Optional[Callable[[str], None]] = None
        self.chain_not_synced_handler: Optional[Callable[[str], None]] = None
        self.display_tor_network_settings_handler: Optional[Callable[[bool], None]] = (
            None
        )
        self.show_first_popup_if_resync_spv_requested_handler: Optional[
            Callable[[], None]
        ] = None
        self.request_wallet_password_handler: Optional[
            Callable[[Callable[[bytes], None]], None]
        ] = None
        self.display_alert_handler: Optional[Callable[["Alert"], None]] = None
        self.display_update_handler: Optional[Callable[["Alert", str], None]] = None
        self.vote_result_exception_handler: Optional[
            Callable[["VoteResultException"], None]
        ] = None
        self.display_private_notification_handler: Optional[
            Callable[["PrivateNotificationPayload"], None]
        ] = None
        self.show_popup_if_invalid_btc_config_handler: Optional[Callable[[], None]] = (
            None
        )
        self.revolut_accounts_update_handler: Optional[
            Callable[[list["RevolutAccount"]], None]
        ] = None
        self.amazon_gift_card_accounts_update_handler: Optional[
            Callable[[list["AmazonGiftCardAccount"]], None]
        ] = None
        self.qubes_os_info_handler: Optional[Callable[[], None]] = None
        self.resync_dao_state_from_resources_handler: Optional[Callable[[], None]] = (
            None
        )
        self.tor_address_upgrade_handler: Optional[Callable[[], None]] = None
        self.down_grade_prevention_handler: Optional[Callable[[str], None]] = None
        # ---------------------------
        # ---------------------------
        self.new_version_available_property = SimpleProperty(False)
        self.p2p_network_ready: Optional["SimpleProperty[bool]"] = None
        self.wallet_initialized = SimpleProperty(False)
        self.all_basic_services_initialized: bool = False
        self.p2p_network_and_wallet_initialized: Optional["SimpleProperty[bool]"] = None
        self.bisq_setup_listeners = set["BisqSetupListener"]()

        MemPoolSpaceTxBroadcaster.init(
            socks5_proxy_provider, preferences, local_bitcoin_node, config
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def display_alert_if_present(self, alert: "Alert", open_new_version_popup: bool):
        if alert is None:
            return

        if alert.is_software_update_notification():
            # only process if the alert version is "newer" than ours
            if alert.is_new_version(self.preferences):
                self.user.set_displayed_alert(alert)  # save context to compare later
                self.new_version_available_property.set(
                    # shows link in footer bar
                    True
                )
                if (
                    alert.can_show_popup(self.preferences) or open_new_version_popup
                ) and self.display_update_handler is not None:
                    self.display_update_handler(alert, alert.show_again_key())
        else:
            # it is a normal message alert
            displayed_alert = self.user.displayed_alert
            if (
                displayed_alert is None or displayed_alert != alert
            ) and self.display_alert_handler is not None:
                self.display_alert_handler(alert)

    def display_offer_disabled_message(self, message: str):
        if self.offer_disabled_handler is not None:
            self.offer_disabled_handler(message)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Main startup tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_bisq_setup_listener(self, listener: "BisqSetupListener"):
        self.bisq_setup_listeners.add(listener)

    def start(self):
        # If user tried to downgrade we require a shutdown
        if (
            self.config.base_currency_network == BaseCurrencyNetwork.BTC_MAINNET
            and self.has_downgraded(self.down_grade_prevention_handler)
        ):
            return

        self.persist_bisq_version()
        self._maybe_resync_spv_chain()
        self._maybe_show_tac(self._step2)

    def _step2(self):
        self._read_maps_from_resources(self._step3)
        self._check_for_correct_os_architecture()
        self._check_if_running_on_qubes_os()

    def _step3(self):
        self._start_p2p_network_and_wallet(self._step4)

    def _step4(self):
        self._init_domain_services()

        for listener in self.bisq_setup_listeners:
            listener.on_setup_complete()

        # We set that after calling the setupCompleteHandler to not trigger a popup from the dev dummy accounts
        # in MainViewModel
        self._maybe_show_security_recommendation()
        self._maybe_show_localhost_running_info()
        self._maybe_show_account_signing_state_info()
        self._maybe_show_tor_address_upgrade_information()
        self._maybe_upgrade_bsq_explorer_url()
        self._check_inbound_connections()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Sub tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _maybe_resync_spv_chain(self):
        # We do the delete of the spv file at startup before BitcoinJ is initialized to avoid issues with locked files under Windows.
        if self.get_resync_spv_semaphore():
            try:
                self.wallets_setup.resync_spv_chain()

                # In case we had an unconfirmed change output we reset the unconfirmedBsqChangeOutputList so that
                # after a SPV resync we do not have any dangling BSQ utxos in that list which would cause an incorrect
                # BSQ balance state after the SPV resync.
                self.unconfirmed_bsq_change_output_list_service.on_spv_resync()
            except Exception as e:
                logger.error(str(e), exc_info=e)

    def _maybe_show_tac(self, next_step: Callable[[], None]):
        if not self.preferences.is_tac_accepted_v120() and not DevEnv.is_dev_mode():
            if self.display_tac_handler is not None:
                self.display_tac_handler(
                    lambda: (self.preferences.set_tac_accepted_v120(True), next_step())
                )
        else:
            next_step()

    def _read_maps_from_resources(self, complete_handler: Callable[[], None]):
        post_fix = "_" + self.config.base_currency_network.name
        # TODO make this async ?
        self.p2p_service.p2p_data_storage.read_from_resources(
            post_fix, complete_handler
        )

    def _start_p2p_network_and_wallet(self, next_step: Callable[[], None]):
        def wallet_initialized_listener(e: SimplePropertyChangeEvent[bool]):
            # JAVA TODO that seems to be called too often if Tor takes longer to start up...
            if (
                e.new_value
                and not self.p2p_network_ready.get()
                and self.display_tor_network_settings_handler
            ):
                self.display_tor_network_settings_handler(True)

        def on_startup_timeout():
            if (
                self.p2p_network_setup.p2p_network_failed.get()
                or self.wallets_setup.wallets_setup_failed.get()
            ):
                # Skip this timeout action if the p2p network or wallet setup failed
                # since an error prompt will be shown containing the error message
                return
            logger.warning("startupTimeout called")
            if self.wallets_manager.are_wallets_encrypted():
                self.wallet_initialized.add_listener(wallet_initialized_listener)
            elif self.display_tor_network_settings_handler:
                self.display_tor_network_settings_handler(True)

        startup_timeout = UserThread.run_after(
            on_startup_timeout, timedelta(minutes=BisqSetup.STARTUP_TIMEOUT_MINUTES)
        )

        logger.info("Init P2P network")
        for listener in self.bisq_setup_listeners:
            listener.on_init_p2p_network()
        self.p2p_network_ready = self.p2p_network_setup.init(
            self._init_wallet, self.display_tor_network_settings_handler
        )

        def transform_p2p_and_wallet_ready(props: list):
            logger.info(f"walletInitialized={props[0]}, p2pNetWorkReady={props[1]}")
            return all(props)

        self.p2p_network_and_wallet_initialized = combine_simple_properties(
            self.wallet_initialized,
            self.p2p_network_ready,
            transform=transform_p2p_and_wallet_ready,
        )

        # // We only init wallet service here if not using Tor for bitcoinj.
        # // When using Tor, wallet init must be deferred until Tor is ready.
        # // JAVA TODO encapsulate below conditional inside getUseTorForBitcoinJ
        if (
            not self.preferences.get_use_tor_for_bitcoin_j()
            or self.local_bitcoin_node.should_be_used()
        ):
            self._init_wallet()

        self.p2p_network_and_wallet_initialized.add_listener(
            lambda e: (
                (
                    startup_timeout.stop(),
                    self.wallet_initialized.remove_listener(
                        wallet_initialized_listener
                    ),
                    (
                        self.display_tor_network_settings_handler(False)
                        if self.display_tor_network_settings_handler
                        else None
                    ),
                    next_step(),
                )
                if e.new_value
                else None
            )
        )

    # TODO REST
    def _init_wallet(self):
        logger.info("Init wallet")
        for listener in self.bisq_setup_listeners:
            listener.on_init_wallet()

        def wallet_password_handler():
            logger.info("Wallet password required")
            for listener in self.bisq_setup_listeners:
                listener.on_request_wallet_password()
            if self.p2p_network_ready.get():
                self.p2p_network_setup.splash_p2p_network_animation_visible.set(True)

            if self.request_wallet_password_handler is not None:

                def on_aes_key_provided(aes_key: bytes):
                    self.wallets_manager.set_aes_key(aes_key)
                    self.wallets_manager.maybe_add_segwit_keychains(aes_key)
                    if self.get_resync_spv_semaphore():
                        if self.show_first_popup_if_resync_spv_requested_handler:
                            self.show_first_popup_if_resync_spv_requested_handler()
                    else:
                        # JAVA TODO no guarantee here that the wallet is really fully initialized
                        # We would need a new walletInitializedButNotEncrypted state to track
                        # Usually init is fast and we have our wallet initialized at that state though.
                        self.wallet_initialized.set(True)

                self.request_wallet_password_handler(on_aes_key_provided)

        self.wallet_app_setup.init(
            self.chain_file_locked_exception_handler,
            self.spv_file_corrupted_handler,
            self.get_resync_spv_semaphore(),
            self.show_first_popup_if_resync_spv_requested_handler,
            self.show_popup_if_invalid_btc_config_handler,
            wallet_password_handler,
            lambda: (
                (
                    # the following are called each time a block is received
                    self._check_for_locked_up_funds(),
                    self._check_for_invalid_maker_fee_txs(),
                    self._check_free_disk_space(),
                )
                if self.all_basic_services_initialized
                else None
            ),
            lambda: self.wallet_initialized.set(True),
        )

    def _init_domain_services(self):
        logger.info("initDomainServices")

        self.domain_initialisation.init_domain_services(
            self.rejected_tx_error_message_handler,
            self.display_private_notification_handler,
            self.dao_error_message_handler,
            self.dao_warn_message_handler,
            self.filter_warning_handler,
            self.chain_not_synced_handler,
            self.offer_disabled_handler,
            self.vote_result_exception_handler,
            self.revolut_accounts_update_handler,
            self.amazon_gift_card_accounts_update_handler,
            self.resync_dao_state_from_resources_handler,
        )

        if self.wallets_setup.download_percentage_property.get() == 1:
            self._check_for_locked_up_funds()
            self._check_for_invalid_maker_fee_txs()

        self.alert_manager.alert_message_property.add_listener(
            lambda e: self.display_alert_if_present(e.new_value, False)
        )
        self.display_alert_if_present(
            self.alert_manager.alert_message_property.get(), False
        )

        self.all_basic_services_initialized = True

        self.app_startup_state.on_domain_services_initialized()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _check_for_locked_up_funds(self):
        # We check if there are locked up funds in failed or closed trades
        try:
            set_of_all_trade_ids = (
                self.trade_manager.get_set_of_failed_or_closed_trade_ids_from_locked_in_funds()
            )
            for entry in self.btc_wallet_service.get_address_entries_for_trade():
                if (
                    entry.offer_id in set_of_all_trade_ids
                    and entry.context == AddressEntryContext.MULTI_SIG
                ):
                    balance = entry.get_coin_locked_in_multi_sig_as_coin()
                    if balance.is_positive():
                        message = Res.get(
                            "popup.warning.lockedUpFunds",
                            self.formatter.format_coin_with_code(balance),
                            entry.get_address_string(),
                            entry.offer_id,
                        )
                        logger.warning(message)
                        if self.locked_up_funds_handler:
                            self.locked_up_funds_handler(message)
        except TradeTxException as e:
            logger.warning(e)
            if self.locked_up_funds_handler:
                self.locked_up_funds_handler(str(e))

    def _check_for_invalid_maker_fee_txs(self):
        # We check if we have open offers with no confidence object at the maker fee tx. That can happen if the
        # miner fee was too low and the transaction got removed from mempool and got out from our wallet after a
        # resync.
        for offer_entry in self.open_offer_manager.get_observable_list():
            if offer_entry.offer.is_bsq_swap_offer:
                continue
            offer_fee_payment_tx_id = offer_entry.offer.offer_fee_payment_tx_id
            if (
                self.btc_wallet_service.get_confidence_for_tx_id(
                    offer_fee_payment_tx_id
                )
                is None
            ):
                message = Res.get(
                    "popup.warning.openOfferWithInvalidMakerFeeTx",
                    offer_entry.offer.short_id,
                    offer_fee_payment_tx_id,
                )
                logger.warning(message)
                if self.locked_up_funds_handler:
                    self.locked_up_funds_handler(message)

    def _check_free_disk_space(self):
        TWO_GIGABYTES = 2147483648

        def on_done(future: Future[int]):
            try:
                usable_space = future.result()
                if usable_space < TWO_GIGABYTES:
                    message = Res.get(
                        "popup.warning.diskSpace",
                        FormattingUtils.format_bytes(usable_space),
                        FormattingUtils.format_bytes(TWO_GIGABYTES),
                    )
                    logger.warning(message)
                    if self.disk_space_warning_handler:
                        self.disk_space_warning_handler(message)
            except Exception as e:
                logger.error(e)

        run_in_thread(
            get_usable_space,
            self.config.app_data_dir,
        ).add_done_callback(on_done)

    def get_last_bisq_version(self) -> Optional[str]:
        version_file = self._get_version_file()
        if not version_file.exists():
            return None
        try:
            with version_file.open() as f:
                # We only expect 1 line
                return f.readline().strip()
        except Exception as e:
            logger.error(e)
        return None

    def get_resync_spv_semaphore(self) -> bool:
        resync_spv_semaphore = self.config.app_data_dir.joinpath(
            BisqSetup.RESYNC_SPV_FILE_NAME
        )
        return resync_spv_semaphore.exists()

    def set_resync_spv_semaphore(self, is_resync_spv_requested: bool):
        resync_spv_semaphore = self.config.app_data_dir.joinpath(
            BisqSetup.RESYNC_SPV_FILE_NAME
        )
        if is_resync_spv_requested:
            if not resync_spv_semaphore.exists():
                try:
                    resync_spv_semaphore.touch(exist_ok=True)
                except Exception as e:
                    logger.error(
                        f"ResyncSpv file could not be created. {e}", exc_info=e
                    )
        else:
            resync_spv_semaphore.unlink(missing_ok=True)

    def _get_version_file(self):
        return self.config.app_data_dir.joinpath(BisqSetup.VERSION_FILE_NAME)

    @staticmethod
    def is_downgrade(last_version: str):
        return last_version and Version.is_new_version(last_version, Version.VERSION)

    def has_downgraded(
        self, down_grade_prevention_handler: Optional[Callable[[str], None]] = None
    ) -> bool:
        last_version = self.get_last_bisq_version()
        has_downgraded = BisqSetup.is_downgrade(last_version)
        if has_downgraded:
            logger.error(
                f"Downgrade from version {last_version} to version {Version.VERSION} is not supported"
            )
            if down_grade_prevention_handler is not None:
                down_grade_prevention_handler(last_version)
        return has_downgraded

    def persist_bisq_version(self):
        version_file = self._get_version_file()
        try:
            with version_file.open("w") as file_writer:
                file_writer.write(Version.VERSION)
        except Exception as e:
            logger.error(f"Writing Version failed. {e}", exc_info=e)

    def _check_for_correct_os_architecture(self):
        # TODO: check later why it's needed
        # I know that some python features used in the project is not available on some platforms,
        # like android, but I don't know if this is necessary here anyway.
        pass

    def _check_if_running_on_qubes_os(self):
        """
        If Bisq is running on an OS that is virtualized under Qubes, show info popup with
        link to the Setup Guide. The guide documents what other steps are needed, in
        addition to installing the Linux package (qube sizing, etc)
        """
        if is_qubes_os() and self.qubes_os_info_handler:
            self.qubes_os_info_handler()

    def _check_inbound_connections(self):
        """
        Check if we have inbound connections.  If not, try to ping ourselves.
        If Bisq cannot connect to its own onion address through Tor, display
        an informative message to let the user know to configure their firewall else
        their offers will not be reachable.
        Repeat this test hourly.
        """
        onion_address = self.p2p_service.address
        if onion_address is None or "onion" not in onion_address.get_full_address():
            return

        if (
            self.p2p_service.network_node.up_time()
            > timedelta(hours=1).total_seconds() * 1000
            and self.p2p_service.network_node.get_inbound_connection_count() == 0
        ):
            # we've been online a while and did not find any inbound connections; lets try the self-ping check
            logger.info(
                "No recent inbound connections found, starting the self-ping test"
            )
            self.private_notification_manager.send_ping(
                onion_address,
                lambda string_result: (
                    logger.info(string_result),
                    (
                        self._notify_ui_that_we_cant_ping_ourself()
                        if "failed" in string_result
                        else None
                    ),
                ),
            )

        # schedule another inbound connection check for later
        next_check_in_minutes = 30 + random.randint(0, 30)
        logger.debug(
            f"Next inbound connections check in {next_check_in_minutes} minutes"
        )
        UserThread.run_after(
            self._check_inbound_connections, timedelta(minutes=next_check_in_minutes)
        )

    def _notify_ui_that_we_cant_ping_ourself(self):
        # TODO
        pass

    def _maybe_show_security_recommendation(self):
        key = "remindPasswordAndBackup"
        self.user.payment_accounts_observable.add_listener(
            lambda change: (
                self.display_security_recommendation_handler(key)
                if (
                    not self.wallets_manager.are_wallets_encrypted()
                    and not self.user.is_payment_account_import
                    and self.preferences.show_again(key)
                    and change.added_elements
                    and self.display_security_recommendation_handler
                )
                else None
            )
        )

    def _maybe_show_localhost_running_info(self):
        if self.config.base_currency_network.is_mainnet():

            def on_done(f: Future[bool]):
                try:
                    should_be_used = f.result()
                    self._maybe_trigger_display_handler(
                        "bitcoinLocalhostNode",
                        self.display_localhost_handler,
                        should_be_used,
                    )
                except:
                    pass

            as_future(self.local_bitcoin_node.should_be_used()).add_done_callback(
                on_done
            )

    def _maybe_show_account_signing_state_info(self):
        key_signed_by_arbitrator = "accountSignedByArbitrator"
        key_signed_by_peer = "accountSignedByPeer"
        key_peer_limit_lifted = "accountLimitLifted"
        key_peer_signer = "accountPeerSigner"

        # check signed witness on startup
        self._check_signing_state(
            AccountAgeWitnessService.SignState.ARBITRATOR,
            key_signed_by_arbitrator,
            self.display_signed_by_arbitrator_handler,
        )
        self._check_signing_state(
            AccountAgeWitnessService.SignState.PEER_INITIAL,
            key_signed_by_peer,
            self.display_signed_by_peer_handler,
        )
        self._check_signing_state(
            AccountAgeWitnessService.SignState.PEER_LIMIT_LIFTED,
            key_peer_limit_lifted,
            self.display_peer_limit_lifted_handler,
        )
        self._check_signing_state(
            AccountAgeWitnessService.SignState.PEER_SIGNER,
            key_peer_signer,
            self.display_peer_signer_handler,
        )

        # check signed witness during runtime
        self.p2p_service.p2p_data_storage.add_append_only_data_store_listener(
            lambda payload: (
                self._maybe_trigger_display_handler(
                    key_signed_by_arbitrator,
                    self.display_signed_by_arbitrator_handler,
                    self._is_signed_witness_of_mine_with_state(
                        payload, AccountAgeWitnessService.SignState.ARBITRATOR
                    ),
                ),
                self._maybe_trigger_display_handler(
                    key_signed_by_peer,
                    self.display_signed_by_peer_handler,
                    self._is_signed_witness_of_mine_with_state(
                        payload, AccountAgeWitnessService.SignState.PEER_INITIAL
                    ),
                ),
                self._maybe_trigger_display_handler(
                    key_peer_limit_lifted,
                    self.display_peer_limit_lifted_handler,
                    self._is_signed_witness_of_mine_with_state(
                        payload, AccountAgeWitnessService.SignState.PEER_LIMIT_LIFTED
                    ),
                ),
                self._maybe_trigger_display_handler(
                    key_peer_signer,
                    self.display_peer_signer_handler,
                    self._is_signed_witness_of_mine_with_state(
                        payload, AccountAgeWitnessService.SignState.PEER_SIGNER
                    ),
                ),
            )
        )

    def _check_signing_state(
        self,
        state: "AccountAgeWitnessService.SignState",
        key: str,
        display_handler: Optional[Callable[[str], None]],
    ):
        signing_state_found = any(
            self._is_signed_witness_of_mine_with_state(payload, state)
            for payload in self.signed_witness_storage_service.get_map().values()
        )
        self._maybe_trigger_display_handler(key, display_handler, signing_state_found)

    def _is_signed_witness_of_mine_with_state(
        self,
        payload: "PersistableNetworkPayload",
        state: "AccountAgeWitnessService.SignState",
    ) -> bool:
        if isinstance(payload, SignedWitness) and self.user.payment_accounts:
            # We know at this point that it is already added to the signed witness list
            # Check if new signed witness is for one of my own accounts
            return any(
                PaymentMethod.has_chargeback_risk(
                    account.payment_method, account.trade_currencies
                )
                and (
                    (
                        signed_witness := self.account_age_witness_service.get_my_witness(
                            account.payment_account_payload
                        )
                    )
                    and signed_witness.get_hash() == payload.account_age_witness_hash
                    and self.account_age_witness_service.get_sign_state(signed_witness)
                    == state
                )
                for account in self.user.payment_accounts
            )
        return False

    def _maybe_trigger_display_handler(
        self,
        key: str,
        display_handler: Optional[Callable[[str], None]],
        signing_state_found: bool,
    ):
        if signing_state_found and self.preferences.show_again(key) and display_handler:
            display_handler(key)

    def _maybe_upgrade_bsq_explorer_url(self):
        # if wiz BSQ explorer selected, replace with 1st explorer in the list of available.
        if (
            self.preferences.get_bsq_block_chain_explorer().name.lower()
            == "mempool.space (@wiz)"
            and len(self.preferences.get_block_chain_explorers()) > 0
        ):
            self.preferences.set_bsq_blockchain_explorer(
                self.preferences.get_bsq_block_chain_explorers()[0]
            )

        if (
            self.preferences.get_bsq_block_chain_explorer().name.lower()
            == "bisq.mempool.emzy.de (@emzy)"
            and len(self.preferences.get_block_chain_explorers()) > 0
        ):
            self.preferences.set_bsq_blockchain_explorer(
                self.preferences.get_bsq_block_chain_explorers()[0]
            )

    def _maybe_show_tor_address_upgrade_information(self):
        # NOTE: This is probably unnecessary and can be removed at some point later
        # we implemented for completeness for now
        if self.config.base_currency_network.is_regtest() or Utils.is_v3_address(
            self.p2p_service.address.host_name
        ):
            return

        self._maybe_run_tor_node_address_upgrade_handler()

        self.trade_manager.num_pending_trades.add_listener(
            lambda e: (
                self._maybe_run_tor_node_address_upgrade_handler()
                if e.new_value == 0
                else None
            )
        )

    def _maybe_run_tor_node_address_upgrade_handler(self):
        if (
            all(
                dispute.is_closed
                for dispute in self.mediation_manager.get_disputes_as_observable_list()
            )
            and all(
                dispute.is_closed
                for dispute in self.refund_manager.get_disputes_as_observable_list()
            )
            and all(
                dispute.is_closed
                for dispute in self.arbitration_manager.get_disputes_as_observable_list()
            )
            and self.trade_manager.num_pending_trades.get() == 0
        ):
            if self.tor_address_upgrade_handler:
                self.tor_address_upgrade_handler()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Wallet
    @property
    def btc_info_property(self):
        return self.wallet_app_setup.btc_info_property

    @property
    def btc_sync_progress_property(self):
        return self.wallet_app_setup.btc_sync_progress_property

    @property
    def wallet_service_error_msg(self):
        return self.wallet_app_setup.wallet_service_error_msg_property

    @property
    def btc_splash_sync_icon_id(self):
        return self.wallet_app_setup.btc_splash_sync_icon_id_property

    @property
    def use_tor_for_btc(self):
        return self.wallet_app_setup.use_tor_for_btc_property

    # P2P
    # TODO: rename properties to have property at the end of their names
    @property
    def p2p_network_info(self):
        return self.p2p_network_setup.p2p_network_info

    @property
    def splash_p2p_network_animation_visible(self):
        return self.p2p_network_setup.splash_p2p_network_animation_visible

    @property
    def p2p_network_warn_msg(self):
        return self.p2p_network_setup.p2p_network_warn_msg

    @property
    def p2p_network_icon_id(self):
        return self.p2p_network_setup.p2p_network_icon_id

    @property
    def p2p_network_status_icon_id(self):
        return self.p2p_network_setup.p2p_network_status_icon_id

    @property
    def data_received(self):
        return self.p2p_network_setup.data_received

    @property
    def p2p_network_label_id(self):
        return self.p2p_network_setup.p2p_network_label_id
