from bisq.common.version import Version
from bisq.core.app.bisq_app import BisqApp


class BisqHeadlessApp(BisqApp):

    def on_setup_complete(self):
        self._logger.info("onSetupComplete")

    def setup_handlers(self):
        bisq_setup = self._user_context.global_container.bisq_setup
        bisq_setup.display_tac_handler = lambda accepted_handler: (
            self._logger.info(
                "onDisplayTacHandler: We accept the tacs automatically in headless mode"
            ),
            accepted_handler(),
        )
        bisq_setup.display_tor_network_settings_handler = (
            lambda show: self._logger.info(
                f"onDisplayTorNetworkSettingsHandler: show={show}"
            )
        )
        bisq_setup.spv_file_corrupted_handler = lambda msg: self._logger.error(
            f"onSpvFileCorruptedHandler: msg={msg}"
        )
        bisq_setup.chain_file_locked_exception_handler = lambda msg: self._logger.error(
            f"onChainFileLockedExceptionHandler: msg={msg}"
        )
        bisq_setup.disk_space_warning_handler = lambda msg: self._logger.error(
            f"onDiskSpaceWarningHandler: msg={msg}"
        )
        bisq_setup.offer_disabled_handler = lambda msg: self._logger.error(
            f"onOfferDisabledHandler: msg={msg}"
        )
        bisq_setup.chain_not_synced_handler = lambda msg: self._logger.error(
            f"onChainNotSyncedHandler: msg={msg}"
        )
        bisq_setup.locked_up_funds_handler = lambda msg: self._logger.info(
            f"onLockedUpFundsHandler: msg={msg}"
        )
        bisq_setup.show_first_popup_if_resync_spv_requested_handler = (
            lambda: self._logger.info("onShowFirstPopupIfResyncSPVRequestedHandler")
        )
        bisq_setup.request_wallet_password_handler = (
            lambda aes_key_handler: self._logger.info("onRequestWalletPasswordHandler")
        )
        bisq_setup.display_update_handler = lambda alert, key: self._logger.info(
            "onDisplayUpdateHandler"
        )
        bisq_setup.display_alert_handler = lambda alert: self._logger.info(
            f"onDisplayAlertHandler. alert={alert}"
        )
        bisq_setup.display_private_notification_handler = lambda private_notification: self._logger.info(
            f"onDisplayPrivateNotificationHandler. privateNotification={private_notification}"
        )
        bisq_setup.dao_error_message_handler = lambda error_message: self._logger.error(
            f"onDaoErrorMessageHandler. errorMessage={error_message}"
        )
        bisq_setup.dao_warn_message_handler = lambda warn_message: self._logger.warning(
            f"onDaoWarnMessageHandler. warnMessage={warn_message}"
        )
        bisq_setup.display_security_recommendation_handler = (
            lambda key: self._logger.info("onDisplaySecurityRecommendationHandler")
        )
        bisq_setup.display_localhost_handler = lambda key: self._logger.info(
            "onDisplayLocalhostHandler"
        )
        bisq_setup.wrong_os_architecture_handler = lambda msg: self._logger.error(
            f"onWrongOSArchitectureHandler. msg={msg}"
        )
        bisq_setup.vote_result_exception_handler = (
            lambda vote_result_exception: self._logger.warning(
                f"voteResultException={vote_result_exception}"
            )
        )
        bisq_setup.rejected_tx_error_message_handler = (
            lambda error_message: self._logger.warning(
                f"setRejectedTxErrorMessageHandler. errorMessage={error_message}"
            )
        )
        bisq_setup.show_popup_if_invalid_btc_config_handler = (
            lambda: self._logger.error("onShowPopupIfInvalidBtcConfigHandler")
        )
        bisq_setup.revolut_accounts_update_handler = lambda revolut_account_list: self._logger.info(
            f"setRevolutAccountsUpdateHandler: revolutAccountList={revolut_account_list}"
        )
        bisq_setup.qubes_os_info_handler = lambda: self._logger.info(
            "setQubesOSInfoHandler"
        )
        bisq_setup.down_grade_prevention_handler = lambda last_version: self._logger.info(
            f"Downgrade from version {last_version} to version {Version.VERSION} is not supported"
        )
        bisq_setup.resync_dao_state_from_resources_handler = lambda: (
            self._logger.warning(
                "There was a problem with synchronizing the DAO state. A restart of the application is required to fix the issue."
            ),
            self._graceful_shut_down_handler.graceful_shut_down(lambda *_: None),
        )
        bisq_setup.tor_address_upgrade_handler = lambda: self._logger.info(
            "setTorAddressUpgradeHandler"
        )

        files = self._corrupted_storage_file_handler.get_files()
        if files:
            self._logger.warning(f"getCorruptedDatabaseFiles. files={files}")

        self._trade_manager.take_offer_request_error_message_handler = (
            lambda _: self._logger.error("onTakeOfferRequestErrorMessageHandler")
        )
