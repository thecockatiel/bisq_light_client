from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.app.headless_app import HeadlessApp
from bisq.common.version import Version

if TYPE_CHECKING:
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.common.file.corrupted_storage_file_handler import (
        CorruptedStorageFileHandler,
    )
    from bisq.core.app.bisq_setup import BisqSetup
    from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
    from global_container import GlobalContainer

logger = get_logger(__name__)


class BisqHeadlessApp(HeadlessApp):
    shut_down_handler: Optional[Callable[[], None]] = None

    def __init__(self):
        self.__shutdown_requested = False
        self.__graceful_shut_down_handler: Optional["GracefulShutDownHandler"] = None
        self._injector: Optional["GlobalContainer"] = None
        self._bisq_setup: Optional["BisqSetup"] = None
        self._corrupted_storage_file_handler: Optional[
            "CorruptedStorageFileHandler"
        ] = None
        self._trade_manager: Optional["TradeManager"] = None

        BisqHeadlessApp.shut_down_handler = self.stop

    @property
    def graceful_shut_down_handler(self) -> "GracefulShutDownHandler":
        return self.__graceful_shut_down_handler

    @graceful_shut_down_handler.setter
    def graceful_shut_down_handler(self, value: "GracefulShutDownHandler"):
        self.__graceful_shut_down_handler = value

    @property
    def injector(self) -> "GlobalContainer":
        return self._injector

    @injector.setter
    def injector(self, injector: "GlobalContainer"):
        self._injector = injector

    def start_application(self):
        try:
            self._bisq_setup = self.injector.bisq_setup
            self._bisq_setup.add_bisq_setup_listener(self)

            self._corrupted_storage_file_handler = (
                self.injector.corrupted_storage_file_handler
            )
            self._trade_manager = self.injector.trade_manager

            self.setup_handlers()
        except Exception as e:
            logger.error("Error during app init", exc_info=e)
            self.handle_uncaught_exception(e, False)

    def on_setup_complete(self):
        logger.info("onSetupComplete")

    def setup_handlers(self):
        # TODO: later we may want to replace these
        # what I have in mind is to always launch headless and launch UI on top of it,
        # so it probably doesn't make sense to automatically accept anything.
        bisq_setup = self._bisq_setup
        bisq_setup.display_tac_handler = lambda accepted_handler: (
            logger.info(
                "onDisplayTacHandler: We accept the tacs automatically in headless mode"
            ),
            accepted_handler(),
        )
        bisq_setup.display_tor_network_settings_handler = lambda show: logger.info(
            f"onDisplayTorNetworkSettingsHandler: show={show}"
        )
        bisq_setup.spv_file_corrupted_handler = lambda msg: logger.error(
            f"onSpvFileCorruptedHandler: msg={msg}"
        )
        bisq_setup.chain_file_locked_exception_handler = lambda msg: logger.error(
            f"onChainFileLockedExceptionHandler: msg={msg}"
        )
        bisq_setup.disk_space_warning_handler = lambda msg: logger.error(
            f"onDiskSpaceWarningHandler: msg={msg}"
        )
        bisq_setup.offer_disabled_handler = lambda msg: logger.error(
            f"onOfferDisabledHandler: msg={msg}"
        )
        bisq_setup.chain_not_synced_handler = lambda msg: logger.error(
            f"onChainNotSyncedHandler: msg={msg}"
        )
        bisq_setup.locked_up_funds_handler = lambda msg: logger.info(
            f"onLockedUpFundsHandler: msg={msg}"
        )
        bisq_setup.show_first_popup_if_resync_spv_requested_handler = (
            lambda: logger.info("onShowFirstPopupIfResyncSPVRequestedHandler")
        )
        bisq_setup.request_wallet_password_handler = (
            lambda aes_key_handler: logger.info("onRequestWalletPasswordHandler")
        )
        bisq_setup.display_update_handler = lambda alert, key: logger.info(
            "onDisplayUpdateHandler"
        )
        bisq_setup.display_alert_handler = lambda alert: logger.info(
            f"onDisplayAlertHandler. alert={alert}"
        )
        bisq_setup.display_private_notification_handler = lambda private_notification: logger.info(
            f"onDisplayPrivateNotificationHandler. privateNotification={private_notification}"
        )
        bisq_setup.dao_error_message_handler = lambda error_message: logger.error(
            f"onDaoErrorMessageHandler. errorMessage={error_message}"
        )
        bisq_setup.dao_warn_message_handler = lambda warn_message: logger.warning(
            f"onDaoWarnMessageHandler. warnMessage={warn_message}"
        )
        bisq_setup.display_security_recommendation_handler = lambda key: logger.info(
            "onDisplaySecurityRecommendationHandler"
        )
        bisq_setup.display_localhost_handler = lambda key: logger.info(
            "onDisplayLocalhostHandler"
        )
        bisq_setup.wrong_os_architecture_handler = lambda msg: logger.error(
            f"onWrongOSArchitectureHandler. msg={msg}"
        )
        bisq_setup.vote_result_exception_handler = (
            lambda vote_result_exception: logger.warning(
                f"voteResultException={vote_result_exception}"
            )
        )
        bisq_setup.rejected_tx_error_message_handler = (
            lambda error_message: logger.warning(
                f"setRejectedTxErrorMessageHandler. errorMessage={error_message}"
            )
        )
        bisq_setup.show_popup_if_invalid_btc_config_handler = lambda: logger.error(
            "onShowPopupIfInvalidBtcConfigHandler"
        )
        bisq_setup.revolut_accounts_update_handler = lambda revolut_account_list: logger.info(
            f"setRevolutAccountsUpdateHandler: revolutAccountList={revolut_account_list}"
        )
        bisq_setup.qubes_os_info_handler = lambda: logger.info("setQubesOSInfoHandler")
        bisq_setup.down_grade_prevention_handler = lambda last_version: logger.info(
            f"Downgrade from version {last_version} to version {Version.VERSION} is not supported"
        )
        bisq_setup.dao_requires_restart_handler = lambda: (
            logger.info(
                "There was a problem with synchronizing the DAO state. A restart of the application is required to fix the issue."
            ),
            self.__graceful_shut_down_handler.graceful_shut_down(lambda: None),
        )
        bisq_setup.tor_address_upgrade_handler = lambda: logger.info(
            "setTorAddressUpgradeHandler"
        )

        files = self._corrupted_storage_file_handler.get_files()
        if files:
            logger.warning(f"getCorruptedDatabaseFiles. files={files}")

        self._trade_manager.take_offer_request_error_message_handler = (
            lambda _: logger.error("onTakeOfferRequestErrorMessageHandler")
        )

    def stop(self):
        if not self.__shutdown_requested:
            UserThread.run_after(
                lambda: self.__graceful_shut_down_handler.graceful_shut_down(
                    lambda: logger.debug("App shutdown complete")
                ),
                timedelta(milliseconds=200),
            )
            self.__shutdown_requested = True

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // UncaughtExceptionHandler implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_uncaught_exception(self, exception: Exception, do_shutdown: bool):
        if not self.__shutdown_requested:
            logger.error(exception)
            if do_shutdown:
                self.stop()
