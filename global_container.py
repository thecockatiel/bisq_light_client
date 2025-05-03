# tried to be in the order of https://github.com/bisq-network/bisq/blob/v1.9.19/core/src/main/java/bisq/core/app/misc/ModuleForAppWithP2p.java

from typing import TYPE_CHECKING

from bisq.common.persistence.persistence_orchestrator import PersistenceOrchestrator
from utils.di import DependencyProvider

if TYPE_CHECKING:
    from shared_container import SharedContainer
    from bisq.core.user.user import User
    from bisq.core.user.preferences import Preferences


class GlobalContainer:
    def __init__(
        self,
        shared_container: "SharedContainer",
        user: "User",
        preferences: "Preferences",
        persistence_orchestrator: "PersistenceOrchestrator",
    ):
        self._shared_container = shared_container
        self._user = user
        self._preferences = preferences
        self._persistence_orchestrator = persistence_orchestrator
        # this is to allow shut_down to free these from instances as well
        self._logger = None
        self._key_ring = None

    def __getattr__(self, name):
        return None

    def shut_down(self):
        # cleanup some refs to allow cleanup
        if self._persistence_proto_resolver:
            self._persistence_proto_resolver._btc_wallet_service_provider = None
            self._persistence_proto_resolver = None

        del self._shared_container

        for key in self.__dict__:
            # we unref the classes we have passed to our instances
            # so that gc can collect them
            if hasattr(self.__dict__[key], "__dict__"):
                for depkey in self.__dict__[key].__dict__:
                    normalized = "_" + depkey.lstrip("_")

                    if normalized in self.__dict__:
                        setattr(self.__dict__[key], depkey, None)
            elif hasattr(self.__dict__[key], "__slots__"):
                for depkey in self.__dict__[key].__slots__:
                    normalized = "_" + depkey.lstrip("_")

                    if normalized in self.__dict__:
                        setattr(self.__dict__[key], depkey, None)

        for key in self.__dict__.copy():
            delattr(self, key)

    @property
    def core_context(self):
        return self._shared_container.core_context

    @property
    def user(self):
        return self._user

    @property
    def preferences(self):
        return self._preferences

    @property
    def persistence_orchestrator(self):
        return self._persistence_orchestrator

    ###############################################################################

    @property
    def btc_network_dir(self):
        if self._btc_network_dir is None:
            self._btc_network_dir = self.user.data_dir.joinpath(
                self.config.base_currency_network.name.lower()
            )
            self._btc_network_dir.mkdir(parents=True, exist_ok=True)
        return self._btc_network_dir

    @property
    def storage_dir(self):
        # reason for this is to rely on user data directory for multi-user feature
        if self._storage_dir is None:
            self._storage_dir = self.btc_network_dir.joinpath("db")
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        return self._storage_dir

    @property
    def wallet_dir(self):
        if self._wallet_dir is None:
            self._wallet_dir = self.user.data_dir.joinpath("electrum_wallet")
            self._wallet_dir.mkdir(parents=True, exist_ok=True)
        return self._wallet_dir

    @property
    def tor_dir(self):
        if self._tor_dir is None:
            self._tor_dir = self.btc_network_dir.joinpath("tor")
            self._tor_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        return self._tor_dir

    ############################################################################### (not listed in ModuleForAppWithP2p)
    @property
    def config(self):
        return self._shared_container.config

    @property
    def bisq_setup(self):
        if self._bisq_setup is None:
            from bisq.core.app.bisq_setup import BisqSetup

            self._bisq_setup = BisqSetup(
                self.domain_initialisation,
                self.p2p_network_setup,
                self.wallet_app_setup,
                self.wallets_manager,
                self.wallets_setup,
                self.btc_wallet_service,
                self.p2p_service,
                self.private_notification_manager,
                self.signed_witness_storage_service,
                self.trade_manager,
                self.open_offer_manager,
                self.preferences,
                self.user,
                self.alert_manager,
                self.unconfirmed_bsq_change_output_list_service,
                self.config,
                self.account_age_witness_service,
                self.btc_formatter,
                self.local_bitcoin_node,
                self.app_startup_state,
                self.socks5_proxy_provider,
                self.mediator_manager,
                self.refund_manager,
                self.arbitration_manager,
            )
        return self._bisq_setup

    @property
    def domain_initialisation(self):
        if self._domain_initialisation is None:
            from bisq.core.app.domain_initialisation import DomainInitialisation

            self._domain_initialisation = DomainInitialisation(
                self.persistence_orchestrator,
                self.clock_watcher,
                self.trade_limits,
                self.arbitration_manager,
                self.mediation_manager,
                self.refund_manager,
                self.trader_chat_manager,
                self.trade_manager,
                self.closed_tradable_manager,
                self.bsq_swap_trade_manager,
                self.failed_trades_manager,
                self.xmr_tx_proof_service,
                self.open_offer_manager,
                self.balances,
                self.wallet_app_setup,
                self.arbitrator_manager,
                self.mediator_manager,
                self.refund_agent_manager,
                self.private_notification_manager,
                self.p2p_service,
                self.fee_service,
                self.dao_setup,
                self.trade_statistics_manager,
                self.account_age_witness_service,
                self.signed_witness_service,
                self.price_feed_service,
                self.filter_manager,
                self.vote_result_service,
                self.mobile_notification_service,
                self.my_offer_taken_events,
                self.trade_events,
                self.dispute_msg_events,
                self.price_alert,
                self.market_alerts,
                self.user,
                self.dao_state_snapshot_service,
                self.trigger_price_service,
                self.mempool_service,
                self.open_bsq_swap_offer_service,
                self.mailbox_message_service,
            )
        return self._domain_initialisation

    @property
    def p2p_network_setup(self):
        if self._p2p_network_setup is None:
            from bisq.common.app.p2p_network_setup import P2PNetworkSetup

            self._p2p_network_setup = P2PNetworkSetup(
                self.price_feed_service,
                self.p2p_service,
                self.preferences,
                self.filter_manager,
            )
        return self._p2p_network_setup

    @property
    def provider(self):
        if self._provider is None:
            from bisq.core.trade.protocol.provider import Provider

            self._provider = Provider(
                self.open_offer_manager,
                self.p2p_service,
                self.btc_wallet_service,
                self.bsq_wallet_service,
                self.trade_wallet_service,
                self.wallets_manager,
                self.dao_facade,
                self.referral_id_service,
                self.user,
                self.filter_manager,
                self.account_age_witness_service,
                self.trade_statistics_manager,
                self.arbitrator_manager,
                self.mediator_manager,
                self.refund_agent_manager,
                self.key_ring,
                self.fee_service,
                self.btc_fee_receiver_service,
                self.delayed_payout_tx_receiver_service,
            )
        return self._provider

    @property
    def corrupted_storage_file_handler(self):
        return self._shared_container.corrupted_storage_file_handler

    @property
    def btc_formatter(self):
        return self._shared_container.btc_formatter

    @property
    def bsq_formatter(self):
        return self._shared_container.bsq_formatter

    @property
    def removed_payloads_service(self):
        if self._removed_payloads_service is None:
            from bisq.core.network.p2p.persistence.removed_payloads_service import (
                RemovedPayloadsService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._removed_payloads_service = RemovedPayloadsService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                )
            )
        return self._removed_payloads_service

    @property
    def mempool_service(self):
        if self._mempool_service is None:
            from bisq.core.provider.mempool.mempool_service import (
                MempoolService,
            )

            self._mempool_service = MempoolService(
                self.socks5_proxy_provider,
                self.config,
                self.preferences,
                self.filter_manager,
                self.dao_facade,
                self.dao_state_service,
                self.burning_man_presentation_service,
            )
        return self._mempool_service

    @property
    def wallet_app_setup(self):
        if self._wallet_app_setup is None:
            from bisq.core.app.wallet_app_setup import WalletAppSetup

            self._wallet_app_setup = WalletAppSetup(
                self.core_context,
                self.wallets_manager,
                self.wallets_setup,
                self.fee_service,
                self.config,
                self.preferences,
            )
        return self._wallet_app_setup

    @property
    def trade_limits(self):
        if self._trade_limits is None:
            from bisq.core.payment.trade_limits import TradeLimits

            self._trade_limits = TradeLimits(self.dao_state_service)
        return self._trade_limits

    @property
    def arbitrator_manager(self):
        if self._arbitrator_manager is None:
            from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import (
                ArbitratorManager,
            )

            self._arbitrator_manager = ArbitratorManager(
                self.key_ring,
                self.arbitrator_service,
                self.user,
                self.filter_manager,
                self.config.use_dev_privilege_keys,
            )
        return self._arbitrator_manager

    @property
    def arbitration_manager(self):
        if self._arbitration_manager is None:
            from bisq.core.support.dispute.arbitration.arbitration_manager import (
                ArbitrationManager,
            )

            self._arbitration_manager = ArbitrationManager(
                self.p2p_service,
                self.trade_wallet_service,
                self.btc_wallet_service,
                self.wallets_setup,
                self.trade_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.open_offer_manager,
                self.dao_facade,
                self.key_ring,
                self.arbitration_dispute_list_service,
                self.config,
                self.price_feed_service,
            )
        return self._arbitration_manager

    @property
    def arbitrator_service(self):
        if self._arbitrator_service is None:
            from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_service import (
                ArbitratorService,
            )

            self._arbitrator_service = ArbitratorService(
                self.p2p_service,
                self.filter_manager,
            )
        return self._arbitrator_service

    @property
    def mediator_manager(self):
        if self._mediator_manager is None:
            from bisq.core.support.dispute.mediation.mediator.mediator_manager import (
                MediatorManager,
            )

            self._mediator_manager = MediatorManager(
                self.key_ring,
                self.mediator_service,
                self.user,
                self.filter_manager,
                self.config.use_dev_privilege_keys,
            )
        return self._mediator_manager

    @property
    def mediation_manager(self):
        if self._mediation_manager is None:
            from bisq.core.support.dispute.mediation.mediation_manager import (
                MediationManager,
            )

            self._mediation_manager = MediationManager(
                self.p2p_service,
                self.trade_wallet_service,
                self.btc_wallet_service,
                self.wallets_setup,
                self.trade_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.open_offer_manager,
                self.dao_facade,
                self.key_ring,
                self.mediation_dispute_list_service,
                self.config,
                self.price_feed_service,
                self.user,
            )
        return self._mediation_manager

    @property
    def mediator_service(self):
        if self._mediator_service is None:
            from bisq.core.support.dispute.mediation.mediator.mediator_service import (
                MediatorService,
            )

            self._mediator_service = MediatorService(
                self.p2p_service,
                self.filter_manager,
            )
        return self._mediator_service

    @property
    def refund_manager(self):
        if self._refund_manager is None:
            from bisq.core.support.refund.refund_manager import (
                RefundManager,
            )

            self._refund_manager = RefundManager(
                self.p2p_service,
                self.trade_wallet_service,
                self.btc_wallet_service,
                self.wallets_setup,
                self.trade_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.open_offer_manager,
                self.dao_facade,
                self.delayed_payout_tx_receiver_service,
                self.key_ring,
                self.refund_dispute_list_service,
                self.config,
                self.price_feed_service,
                self.mempool_service,
            )
        return self._refund_manager

    @property
    def refund_agent_manager(self):
        if self._refund_agent_manager is None:
            from bisq.core.support.refund.refundagent.refund_agent_manager import (
                RefundAgentManager,
            )

            self._refund_agent_manager = RefundAgentManager(
                self.key_ring,
                self.refund_agent_service,
                self.user,
                self.filter_manager,
                self.config.use_dev_privilege_keys,
            )
        return self._refund_agent_manager

    @property
    def refund_agent_service(self):
        if self._refund_agent_service is None:
            from bisq.core.support.refund.refundagent.refund_agent_service import (
                RefundAgentService,
            )

            self._refund_agent_service = RefundAgentService(
                self.p2p_service,
                self.filter_manager,
            )
        return self._refund_agent_service

    @property
    def arbitration_dispute_list_service(self):
        if self._arbitration_dispute_list_service is None:
            from bisq.core.support.dispute.arbitration.arbitration_dispute_list_service import (
                ArbitrationDisputeListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._arbitration_dispute_list_service = ArbitrationDisputeListService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                )
            )
        return self._arbitration_dispute_list_service

    @property
    def mediation_dispute_list_service(self):
        if self._mediation_dispute_list_service is None:
            from bisq.core.support.dispute.mediation.mediation_dispute_list_service import (
                MediationDisputeListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._mediation_dispute_list_service = MediationDisputeListService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                )
            )
        return self._mediation_dispute_list_service

    @property
    def refund_dispute_list_service(self):
        if self._refund_dispute_list_service is None:
            from bisq.core.support.refund.refund_dispute_list_service import (
                RefundDisputeListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._refund_dispute_list_service = RefundDisputeListService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                )
            )
        return self._refund_dispute_list_service

    @property
    def trader_chat_manager(self):
        if self._trader_chat_manager is None:
            from bisq.core.support.traderchat.trader_chat_manager import (
                TraderChatManager,
            )

            self._trader_chat_manager = TraderChatManager(
                self.p2p_service,
                self.wallets_setup,
                self.trade_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.key_ring.pub_key_ring,
            )
        return self._trader_chat_manager

    @property
    def mailbox_message_service(self):
        if self._mailbox_message_service is None:
            from bisq.core.network.p2p.mailbox.mailbox_message_service import (
                MailboxMessageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._mailbox_message_service = MailboxMessageService(
                self.network_node,
                self.peer_manager,
                self.p2p_data_storage,
                self.encryption_service,
                self.ignored_mailbox_service,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.key_ring,
                self.clock,
                self.config.republish_mailbox_entries,
            )
        return self._mailbox_message_service

    @property
    def ignored_mailbox_service(self):
        if self._ignored_mailbox_service is None:
            from bisq.core.network.p2p.mailbox.ignored_mailbox_service import (
                IgnoredMailboxService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._ignored_mailbox_service = IgnoredMailboxService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )
        return self._ignored_mailbox_service

    @property
    def bsq_swap_trade_manager(self):
        if self._bsq_swap_trade_manager is None:
            from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import (
                BsqSwapTradeManager,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._bsq_swap_trade_manager = BsqSwapTradeManager(
                self.key_ring,
                self.price_feed_service,
                self.bsq_wallet_service,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )
        return self._bsq_swap_trade_manager

    @property
    def trade_statistics_2_storage_service(self):
        if self._trade_statistics_2_storage_service is None:
            from bisq.core.trade.statistics.trade_statistics_2_storage_service import (
                TradeStatistics2StorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._trade_statistics_2_storage_service = TradeStatistics2StorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )
        return self._trade_statistics_2_storage_service

    @property
    def trade_statistics_3_storage_service(self):
        if self._trade_statistics_3_storage_service is None:
            from bisq.core.trade.statistics.trade_statistics_3_storage_service import (
                TradeStatistics3StorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._trade_statistics_3_storage_service = TradeStatistics3StorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )
        return self._trade_statistics_3_storage_service

    @property
    def trade_statistics_converter(self):
        if self._trade_statistics_converter is None:
            from bisq.core.trade.statistics.trade_statistics_converter import (
                TradeStatisticsConverter,
            )

            self._trade_statistics_converter = TradeStatisticsConverter(
                self.p2p_service,
                self.p2p_data_storage,
                self.trade_statistics_2_storage_service,
                self.trade_statistics_3_storage_service,
                self.append_only_data_store_service,
                self.storage_dir,
            )
        return self._trade_statistics_converter

    @property
    def trade_statistics_manager(self):
        if self._trade_statistics_manager is None:
            from bisq.core.trade.statistics.trade_statistics_manager import (
                TradeStatisticsManager,
            )

            self._trade_statistics_manager = TradeStatisticsManager(
                self.p2p_service,
                self.price_feed_service,
                self.trade_statistics_3_storage_service,
                self.append_only_data_store_service,
                self.trade_statistics_converter,
                self.storage_dir,
                self.config.dump_statistics,
            )
        return self._trade_statistics_manager

    @property
    def trade_util(self):
        if self._trade_util is None:
            from bisq.core.trade.bisq_v1.trade_util import TradeUtil

            self._trade_util = TradeUtil(
                self.btc_wallet_service,
                self.key_ring,
            )
        return self._trade_util

    @property
    def wallets_manager(self):
        if self._wallets_manager is None:
            from bisq.core.btc.wallet.wallets_manager import WalletsManager

            self._wallets_manager = WalletsManager(
                self.btc_wallet_service,
                self.trade_wallet_service,
                self.bsq_wallet_service,
                self.wallets_setup,
            )
        return self._wallets_manager

    @property
    def btc_fee_receiver_service(self):
        if self._btc_fee_receiver_service is None:
            from bisq.core.dao.burningman.btc_fee_receiver_service import (
                BtcFeeReceiverService,
            )

            self._btc_fee_receiver_service = BtcFeeReceiverService(
                self.dao_state_service,
                self.burning_man_service,
            )
        return self._btc_fee_receiver_service

    @property
    def dump_delayed_payout_tx(self):
        if self._dump_delayed_payout_tx is None:
            from bisq.core.trade.bisq_v1.dump_delayed_payout_tx import (
                DumpDelayedPayoutTx,
            )

            self._dump_delayed_payout_tx = DumpDelayedPayoutTx(
                self.storage_dir,
                self.config.dump_delayed_payout_txs,
            )
        return self._dump_delayed_payout_tx

    @property
    def create_offer_service(self):
        if self._create_offer_service is None:
            from bisq.core.offer.bisq_v1.create_offer_service import CreateOfferService

            self._create_offer_service = CreateOfferService(
                self.offer_util,
                self.tx_fee_estimation_service,
                self.price_feed_service,
                self.p2p_service,
                self.key_ring.pub_key_ring,
                self.user,
                self.btc_wallet_service,
            )
        return self._create_offer_service

    @property
    def offer_util(self):
        if self._offer_util is None:
            from bisq.core.offer.offer_util import OfferUtil

            self._offer_util = OfferUtil(
                self.account_age_witness_service,
                self.bsq_wallet_service,
                self.filter_manager,
                self.preferences,
                self.price_feed_service,
                self.p2p_service,
                self.referral_id_service,
                self.trade_statistics_manager,
            )
        return self._offer_util

    @property
    def cleanup_mailbox_messages_service(self):
        if self._cleanup_mailbox_messages_service is None:
            from bisq.core.trade.bisq_v1.cleanup_mailbox_message_service import (
                CleanupMailboxMessagesService,
            )

            self._cleanup_mailbox_messages_service = CleanupMailboxMessagesService(
                self.p2p_service, self.mailbox_message_service
            )
        return self._cleanup_mailbox_messages_service

    @property
    def xmr_tx_proof_service(self):
        if self._xmr_tx_proof_service is None:
            from bisq.core.trade.txproof.xmr.xmr_tx_proof_service import (
                XmrTxProofService,
            )

            self._xmr_tx_proof_service = XmrTxProofService(
                self.filter_manager,
                self.preferences,
                self.trade_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.mediation_manager,
                self.refund_manager,
                self.p2p_service,
                self.wallets_setup,
                self.socks5_proxy_provider,
            )
        return self._xmr_tx_proof_service

    @property
    def mobile_message_encryption(self):
        if self._mobile_message_encryption is None:
            from bisq.core.notifications.mobile_message_encryption import (
                MobileMessageEncryption,
            )

            self._mobile_message_encryption = MobileMessageEncryption()
        return self._mobile_message_encryption

    @property
    def mobile_notification_validator(self):
        if self._mobile_notification_validator is None:
            from bisq.core.notifications.mobile_notification_validator import (
                MobileNotificationValidator,
            )

            self._mobile_notification_validator = MobileNotificationValidator()
        return self._mobile_notification_validator

    @property
    def mobile_model(self):
        if self._mobile_model is None:
            from bisq.core.notifications.mobile_model import MobileModel

            self._mobile_model = MobileModel()
        return self._mobile_model

    @property
    def mobile_notification_service(self):
        if self._mobile_notification_service is None:
            from bisq.core.notifications.mobile_notification_service import (
                MobileNotificationService,
            )

            self._mobile_notification_service = MobileNotificationService(
                self.preferences,
                self.mobile_message_encryption,
                self.mobile_notification_validator,
                self.mobile_model,
                self.http_client,
                self.config.use_localhost_for_p2p,
            )
        return self._mobile_notification_service

    @property
    def my_offer_taken_events(self):
        if self._my_offer_taken_events is None:
            from bisq.core.notifications.alerts.my_offer_taken_events import (
                MyOfferTakenEvents,
            )

            self._my_offer_taken_events = MyOfferTakenEvents(
                self.mobile_notification_service,
                self.open_offer_manager,
            )
        return self._my_offer_taken_events

    @property
    def trade_events(self):
        if self._trade_events is None:
            from bisq.core.notifications.alerts.trade_events import (
                TradeEvents,
            )

            self._trade_events = TradeEvents(
                self.trade_manager,
                self.key_ring,
                self.mobile_notification_service,
            )
        return self._trade_events

    @property
    def dispute_msg_events(self):
        if self._dispute_msg_events is None:
            from bisq.core.notifications.alerts.dispute_msg_events import (
                DisputeMsgEvents,
            )

            self._dispute_msg_events = DisputeMsgEvents(
                self.refund_manager,
                self.mediation_manager,
                self.p2p_service,
                self.mobile_notification_service,
            )
        return self._dispute_msg_events

    @property
    def price_alert(self):
        if self._price_alert is None:
            from bisq.core.notifications.alerts.price.price_alert import PriceAlert

            self._price_alert = PriceAlert(
                self.price_feed_service,
                self.mobile_notification_service,
                self.user,
            )
        return self._price_alert

    @property
    def market_alerts(self):
        if self._market_alerts is None:
            from bisq.core.notifications.alerts.market.market_alerts import MarketAlerts

            self._market_alerts = MarketAlerts(
                self.offer_book_service,
                self.mobile_notification_service,
                self.user,
                self.price_feed_service,
                self.key_ring,
            )
        return self._market_alerts

    @property
    def trigger_price_service(self):
        if self._trigger_price_service is None:
            from bisq.core.offer.bisq_v1.trigger_price_service import (
                TriggerPriceService,
            )

            self._trigger_price_service = TriggerPriceService(
                self.p2p_service,
                self.open_offer_manager,
                self.mempool_service,
                self.price_feed_service,
            )
        return self._trigger_price_service

    @property
    def open_bsq_swap_offer_service(self):
        if self._open_bsq_swap_offer_service is None:
            from bisq.core.offer.bsq_swap.open_bsq_swap_offer_service import (
                OpenBsqSwapOfferService,
            )

            self._open_bsq_swap_offer_service = OpenBsqSwapOfferService(
                self.open_offer_manager,
                self.btc_wallet_service,
                self.bsq_wallet_service,
                self.fee_service,
                self.p2p_service,
                self.dao_facade,
                self.offer_book_service,
                self.offer_util,
                self.filter_manager,
                self.key_ring.pub_key_ring,
            )
        return self._open_bsq_swap_offer_service

    @property
    def local_bitcoin_node(self):
        if self._local_bitcoin_node is None:
            from bisq.core.btc.nodes.local_bitcoin_node import (
                LocalBitcoinNode,
            )

            self._local_bitcoin_node = LocalBitcoinNode(self.config)
        return self._local_bitcoin_node

    @property
    def app_startup_state(self):
        if self._app_startup_state is None:
            from bisq.core.app.app_startup_state import (
                AppStartupState,
            )

            self._app_startup_state = AppStartupState(
                self.wallets_setup,
                self.p2p_service,
            )
        return self._app_startup_state

    ############################################################################### ModuleForAppWithP2p

    @property
    def key_ring(self):
        return self.user.key_ring

    @property
    def clock_watcher(self):
        return self._shared_container.clock_watcher

    @property
    def network_proto_resolver(self):
        return self._shared_container.network_proto_resolver

    @property
    def persistence_proto_resolver(self):
        if self._persistence_proto_resolver is None:
            from bisq.core.protocol.persistable.core_persistence_proto_resolver import (
                CorePersistenceProtoResolver,
            )
            from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService

            class BtcWalletServiceProvider(DependencyProvider["BtcWalletService"]):
                def get(self_) -> "BtcWalletService":
                    return self.btc_wallet_service

            self._persistence_proto_resolver = CorePersistenceProtoResolver(
                self.clock,
                BtcWalletServiceProvider(),
                self.network_proto_resolver,
            )
        return self._persistence_proto_resolver

    @property
    def bridge_address_provider(self):
        if self._bridge_address_provider is None:
            self._bridge_address_provider = self.preferences

        return self._bridge_address_provider

    @property
    def tor_setup(self):
        if self._tor_setup is None:
            from bisq.common.app.tor_setup import TorSetup

            self._tor_setup = TorSetup(self.tor_dir)

        return self._tor_setup

    @property
    def seed_node_repository(self):
        if self._seed_node_repository is None:
            from bisq.core.network.p2p.seed.default_seed_node_repository import (
                DefaultSeedNodeRepository,
            )

            self._seed_node_repository = DefaultSeedNodeRepository(self.config)

        return self._seed_node_repository

    @property
    def ban_filter(self):
        if self._ban_filter is None:
            from bisq.core.network.core_ban_filter import CoreBanFilter

            self._ban_filter = CoreBanFilter(self.config.ban_list)

        return self._ban_filter

    ###############################################################################

    @property
    def delayed_payout_tx_receiver_service(self):
        if self._delayed_payout_tx_receiver_service is None:
            from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
                DelayedPayoutTxReceiverService,
            )

            self._delayed_payout_tx_receiver_service = DelayedPayoutTxReceiverService(
                self.dao_state_service, self.burning_man_service
            )
        return self._delayed_payout_tx_receiver_service

    @property
    def burning_man_service(self):
        if self._burning_man_service is None:
            from bisq.core.dao.burningman.burning_man_service import BurningManService

            self._burning_man_service = BurningManService(
                self.dao_state_service,
                self.cycles_in_dao_state_service,
                self.proposal_service,
            )
        return self._burning_man_service

    @property
    def burn_target_service(self):
        if self._burn_target_service is None:
            from bisq.core.dao.burningman.burn_target_service import BurnTargetService

            self._burn_target_service = BurnTargetService(
                self.dao_state_service,
                self.cycles_in_dao_state_service,
                self.proposal_service,
            )
        return self._burn_target_service

    @property
    def burning_man_presentation_service(self):
        if self._burning_man_presentation_service is None:
            from bisq.core.dao.burningman.burning_man_presentation_service import (
                BurningManPresentationService,
            )

            self._burning_man_presentation_service = BurningManPresentationService(
                self.dao_state_service,
                self.cycles_in_dao_state_service,
                self.my_proposal_list_service,
                self.bsq_wallet_service,
                self.burning_man_service,
                self.burn_target_service,
            )
        return self._burning_man_presentation_service

    @property
    def burning_man_accounting_service(self):
        if self._burning_man_accounting_service is None:
            from bisq.core.dao.burningman.burning_man_accounting_service import (
                BurningManAccountingService,
            )

            self._burning_man_accounting_service = BurningManAccountingService(
                self.dao_state_service,
                self.burning_man_accounting_store_service,
                self.burning_man_presentation_service,
                self.trade_statistics_manager,
                self.preferences,
            )
        return self._burning_man_accounting_service

    @property
    def burning_man_accounting_store_service(self):
        if self._burning_man_accounting_store_service is None:
            from bisq.core.dao.burningman.accounting.storage.burning_man_accounting_store_service import (
                BurningManAccountingStoreService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._burning_man_accounting_store_service = (
                BurningManAccountingStoreService(
                    self.resource_data_store_service,
                    self.storage_dir,
                    PersistenceManager(
                        self.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                        self.persistence_orchestrator,
                    ),
                )
            )
        return self._burning_man_accounting_store_service

    ###############################################################################
    @property
    def trade_manager(self):
        if self._trade_manager is None:
            from bisq.core.trade.trade_manager import TradeManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._trade_manager = TradeManager(
                self.user,
                self.key_ring,
                self.btc_wallet_service,
                self.bsq_wallet_service,
                self.open_offer_manager,
                self.closed_tradable_manager,
                self.bsq_swap_trade_manager,
                self.failed_trades_manager,
                self.p2p_service,
                self.price_feed_service,
                self.trade_statistics_manager,
                self.trade_util,
                self.arbitrator_manager,
                self.mediator_manager,
                self.provider,
                self.clock_watcher,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.referral_id_service,
                self.persistence_proto_resolver,
                self.dump_delayed_payout_tx,
                self.config.allow_faulty_delayed_txs,
            )
        return self._trade_manager

    @property
    def closed_tradable_manager(self):
        if self._closed_tradable_manager is None:
            from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._closed_tradable_manager = ClosedTradableManager(
                self.key_ring,
                self.price_feed_service,
                self.bsq_swap_trade_manager,
                self.bsq_wallet_service,
                self.preferences,
                self.trade_statistics_manager,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.cleanup_mailbox_messages_service,
                self.dump_delayed_payout_tx,
            )
        return self._closed_tradable_manager

    @property
    def closed_tradable_formatter(self):
        if self._closed_tradable_formatter is None:
            from bisq.core.trade.closed_tradable_formatter import (
                ClosedTradableFormatter,
            )

            self._closed_tradable_formatter = ClosedTradableFormatter(
                self.closed_tradable_manager,
                self.bsq_formatter,
                self.btc_formatter,
                self.bsq_wallet_service,
            )
        return self._closed_tradable_formatter

    @property
    def failed_trades_manager(self):
        if self._failed_trades_manager is None:
            from bisq.core.trade.bisq_v1.failed_trades_manager import (
                FailedTradesManager,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._failed_trades_manager = FailedTradesManager(
                self.key_ring,
                self.price_feed_service,
                self.btc_wallet_service,
                self.preferences,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.trade_util,
                self.cleanup_mailbox_messages_service,
                self.dump_delayed_payout_tx,
                self.config.allow_faulty_delayed_txs,
            )
        return self._failed_trades_manager

    @property
    def take_offer_model(self):
        if self._take_offer_model is None:
            from bisq.core.offer.bisq_v1.take_offer_model import TakeOfferModel

            self._take_offer_model = TakeOfferModel(
                self.account_age_witness_service,
                self.btc_wallet_service,
                self.fee_service,
                self.offer_util,
                self.price_feed_service,
            )
        return self._take_offer_model

    @property
    def bsq_swap_take_offer_model(self):
        if self._bsq_swap_take_offer_model is None:
            from bisq.core.offer.bsq_swap.bsq_swap_take_offer_model import (
                BsqSwapTakeOfferModel,
            )

            self._bsq_swap_take_offer_model = BsqSwapTakeOfferModel(
                self.offer_util,
                self.btc_wallet_service,
                self.bsq_wallet_service,
                self.fee_service,
                self.trade_manager,
                self.filter_manager,
            )
        return self._bsq_swap_take_offer_model

    @property
    def account_age_witness_service(self):
        if self._account_age_witness_service is None:
            from bisq.core.account.witness.account_age_witness_service import (
                AccountAgeWitnessService,
            )

            self._account_age_witness_service = AccountAgeWitnessService(
                self.key_ring,
                self.p2p_service,
                self.user,
                self.signed_witness_service,
                self.account_age_witness_storage_service,
                self.append_only_data_store_service,
                self.clock,
                self.preferences,
                self.filter_manager,
            )
        return self._account_age_witness_service

    @property
    def account_age_witness_storage_service(self):
        if self._account_age_witness_storage_service is None:
            from bisq.core.account.witness.account_age_witness_storage_service import (
                AccountAgeWitnessStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._account_age_witness_storage_service = AccountAgeWitnessStorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )
        return self._account_age_witness_storage_service

    @property
    def signed_witness_service(self):
        if self._signed_witness_service is None:
            from bisq.core.account.sign.signed_witness_service import (
                SignedWitnessService,
            )

            self._signed_witness_service = SignedWitnessService(
                self.key_ring,
                self.p2p_service,
                self.arbitrator_manager,
                self.signed_witness_storage_service,
                self.append_only_data_store_service,
                self.user,
                self.filter_manager,
            )
        return self._signed_witness_service

    @property
    def signed_witness_storage_service(self):
        if self._signed_witness_storage_service is None:
            from bisq.core.account.sign.signed_witness_storage_service import (
                SignedWitnessStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._signed_witness_storage_service = SignedWitnessStorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )
        return self._signed_witness_storage_service

    @property
    def referral_id_service(self):
        if self._referral_id_service is None:
            from bisq.core.trade.statistics.referral_id_service import ReferralIdService

            self._referral_id_service = ReferralIdService(self.preferences)
        return self._referral_id_service

    ############################################################################### EncryptionServiceModule
    @property
    def encryption_service(self):
        if self._encryption_service is None:
            from bisq.core.network.crypto.encryption_service import EncryptionService

            self._encryption_service = EncryptionService(
                self.key_ring, self.network_proto_resolver
            )
        return self._encryption_service

    ############################################################################### OfferModule
    @property
    def open_offer_manager(self):
        if self._open_offer_manager is None:
            from bisq.core.offer.open_offer_manager import OpenOfferManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._open_offer_manager = OpenOfferManager(
                self.core_context,
                self.create_offer_service,
                self.key_ring,
                self.user,
                self.p2p_service,
                self.btc_wallet_service,
                self.trade_wallet_service,
                self.bsq_wallet_service,
                self.offer_book_service,
                self.closed_tradable_manager,
                self.price_feed_service,
                self.preferences,
                self.trade_statistics_manager,
                self.arbitrator_manager,
                self.mediator_manager,
                self.refund_agent_manager,
                self.dao_facade,
                self.filter_manager,
                self.btc_fee_receiver_service,
                self.delayed_payout_tx_receiver_service,
                self.broadcaster,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.dao_state_service,
            )
        return self._open_offer_manager

    @property
    def offer_book_service(self):
        if self._offer_book_service is None:
            from bisq.core.offer.offer_book_service import OfferBookService

            self._offer_book_service = OfferBookService(
                self.p2p_service,
                self.price_feed_service,
                self.filter_manager,
                self.storage_dir,
                self.config.dump_statistics,
            )
        return self._offer_book_service

    @property
    def offer_filter_service(self):
        if self._offer_filter_service is None:
            from bisq.core.offer.offer_filter_service import OfferFilterService

            self._offer_filter_service = OfferFilterService(
                self.user,
                self.preferences,
                self.filter_manager,
                self.account_age_witness_service,
            )
        return self._offer_filter_service

    ############################################################################### P2PModule
    @property
    def clock(self):
        return self._shared_container.clock

    @property
    def p2p_service(self):
        if self._p2p_service is None:
            from bisq.core.network.p2p.p2p_service import P2PService

            self._p2p_service = P2PService(
                network_node=self.network_node,
                peer_manager=self.peer_manager,
                p2p_data_storage=self.p2p_data_storage,
                request_data_manager=self.request_data_manager,
                peer_exchange_manager=self.peer_exchange_manager,
                keep_alive_manager=self.keep_alive_manager,
                broadcaster=self.broadcaster,
                socks5_proxy_provider=self.socks5_proxy_provider,
                encryption_service=self.encryption_service,
                key_ring=self.key_ring,
                mailbox_message_service=self.mailbox_message_service,
            )

        return self._p2p_service

    @property
    def peer_manager(self):
        if self._peer_manager is None:
            from bisq.core.network.p2p.peers.peer_manager import PeerManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._peer_manager = PeerManager(
                self.network_node,
                self.seed_node_repository,
                self.clock_watcher,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.config.max_connections,
            )

        return self._peer_manager

    @property
    def p2p_data_storage(self):
        if self._p2p_data_storage is None:
            from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._p2p_data_storage = P2PDataStorage(
                self.network_node,
                self.broadcaster,
                self.append_only_data_store_service,
                self.protected_data_store_service,
                self.resource_data_store_service,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.removed_payloads_service,
                self.clock,
                self.config.MAX_SEQUENCE_NUMBER_MAP_SIZE_BEFORE_PURGE,
            )

        return self._p2p_data_storage

    @property
    def append_only_data_store_service(self):
        if self._append_only_data_store_service is None:
            from bisq.core.network.p2p.persistence.append_only_data_store_service import (
                AppendOnlyDataStoreService,
            )

            self._append_only_data_store_service = AppendOnlyDataStoreService()

        return self._append_only_data_store_service

    @property
    def protected_data_store_service(self):
        if self._protected_data_store_service is None:
            from bisq.core.network.p2p.persistence.protected_data_store_service import (
                ProtectedDataStoreService,
            )

            self._protected_data_store_service = ProtectedDataStoreService()

        return self._protected_data_store_service

    @property
    def resource_data_store_service(self):
        if self._resource_data_store_service is None:
            from bisq.core.network.p2p.storage.persistence.resource_data_store_service import (
                ResourceDataStoreService,
            )

            self._resource_data_store_service = ResourceDataStoreService()

        return self._resource_data_store_service

    @property
    def request_data_manager(self):
        if self._request_data_manager is None:
            from bisq.core.network.p2p.peers.getdata.request_data_manager import (
                RequestDataManager,
            )

            self._request_data_manager = RequestDataManager(
                self.network_node,
                self.seed_node_repository,
                self.p2p_data_storage,
                self.peer_manager,
            )

        return self._request_data_manager

    @property
    def peer_exchange_manager(self):
        if self._peer_exchange_manager is None:
            from bisq.core.network.p2p.peers.peerexchange.peer_exchange_manager import (
                PeerExchangeManager,
            )

            self._peer_exchange_manager = PeerExchangeManager(
                self.network_node,
                self.seed_node_repository,
                self.peer_manager,
            )

        return self._peer_exchange_manager

    @property
    def keep_alive_manager(self):
        if self._keep_alive_manager is None:
            from bisq.core.network.p2p.peers.keepalive.keep_alive_manager import (
                KeepAliveManager,
            )

            self._keep_alive_manager = KeepAliveManager(
                self.network_node,
                self.peer_manager,
            )

        return self._keep_alive_manager

    @property
    def broadcaster(self):
        if self._broadcaster is None:
            from bisq.core.network.p2p.peers.broadcaster import Broadcaster

            self._broadcaster = Broadcaster(
                self.network_node,
                self.peer_manager,
                self.config.max_connections,
            )

        return self._broadcaster

    @property
    def network_node_provider(self):
        if self._network_node_provider is None:
            from bisq.core.network.p2p.network_node_provider import NetworkNodeProvider

            self._network_node_provider = NetworkNodeProvider(
                self.network_proto_resolver,
                self.bridge_address_provider,
                self.ban_filter,
                self.config,
                self.tor_dir,
            )

        return self._network_node_provider

    @property
    def network_node(self):
        if self._network_node is None:
            self._network_node = self.network_node_provider.get()

        return self._network_node

    @property
    def socks5_proxy_provider(self):
        if self._socks5_proxy_provider is None:
            from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider

            self._socks5_proxy_provider = Socks5ProxyProvider(
                self.config.socks5_proxy_btc_address,
                self.config.socks5_proxy_http_address,
            )

        return self._socks5_proxy_provider

    @property
    def http_client(self):
        if self._http_client is None:
            from bisq.core.network.http.async_http_client_impl import (
                AsyncHttpClientImpl,
            )

            self._http_client = AsyncHttpClientImpl(None, self.socks5_proxy_provider)

        return self._http_client

    ############################################################################### BitcoinModule
    @property
    def address_entry_list(self):
        if self._address_entry_list is None:
            from bisq.core.btc.model.address_entry_list import AddressEntryList
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._address_entry_list = AddressEntryList(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._address_entry_list

    @property
    def wallets_setup(self):
        if self._wallets_setup is None:
            from bisq.core.btc.setup.wallets_setup import WalletsSetup

            self._wallets_setup = WalletsSetup(
                self.address_entry_list,
                self.preferences,
                self.socks5_proxy_provider,
                self.config,
                self.wallet_dir,
            )

        return self._wallets_setup

    @property
    def btc_wallet_service(self):
        if self._btc_wallet_service is None:
            from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService

            self._btc_wallet_service = BtcWalletService(
                self.wallets_setup,
                self.address_entry_list,
                self.preferences,
                self.fee_service,
            )

        return self._btc_wallet_service

    @property
    def bsq_wallet_service(self):
        if self._bsq_wallet_service is None:
            from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService

            self._bsq_wallet_service = BsqWalletService(
                self.wallets_setup,
                self.bsq_coin_selector,
                self.non_bsq_coin_selector,
                self.dao_state_service,
                self.unconfirmed_bsq_change_output_list_service,
                self.preferences,
                self.fee_service,
                self.dao_kill_switch,
                self.bsq_formatter,
            )

        return self._bsq_wallet_service

    @property
    def bsq_transfer_service(self):
        if self._bsq_transfer_service is None:
            from bisq.core.btc.wallet.bsq_transfer_service import BsqTransferService

            self._bsq_transfer_service = BsqTransferService(
                self.wallets_manager,
                self.bsq_wallet_service,
                self.btc_wallet_service,
            )

        return self._bsq_transfer_service

    @property
    def trade_wallet_service(self):
        if self._trade_wallet_service is None:
            from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService

            self._trade_wallet_service = TradeWalletService(
                self.wallets_setup,
                self.preferences,
            )

        return self._trade_wallet_service

    @property
    def bsq_coin_selector(self):
        if self._bsq_coin_selector is None:
            from bisq.core.btc.wallet.bsq_coin_selector import BsqCoinSelector

            self._bsq_coin_selector = BsqCoinSelector(
                self.dao_state_service,
                self.unconfirmed_bsq_change_output_list_service,
            )

        return self._bsq_coin_selector

    @property
    def non_bsq_coin_selector(self):
        if self._non_bsq_coin_selector is None:
            from bisq.core.btc.wallet.non_bsq_coin_selector import NonBsqCoinSelector

            self._non_bsq_coin_selector = NonBsqCoinSelector(
                self.dao_state_service,
                self.preferences,
            )

        return self._non_bsq_coin_selector

    @property
    def price_feed_node_address_provider(self):
        if self._providers_repository is None:
            from bisq.core.provider.price_feed_node_address_provider import (
                PriceFeedNodeAddressProvider,
            )

            self._providers_repository = PriceFeedNodeAddressProvider(
                self.config,
                self.config.providers,
                self.config.use_localhost_for_p2p,
            )

        return self._providers_repository

    @property
    def balances(self):
        if self._balances is None:
            from bisq.core.btc.balances import Balances

            self._balances = Balances(
                self.trade_manager,
                self.btc_wallet_service,
                self.open_offer_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.refund_manager,
            )

        return self._balances

    @property
    def price_feed_service(self):
        if self._price_feed_service is None:
            from bisq.core.provider.price.price_feed_service import PriceFeedService
            from bisq.core.provider.price_http_client import PriceHttpClient

            self._price_feed_service = PriceFeedService(
                PriceHttpClient(None, self.socks5_proxy_provider),
                self.p2p_service,
                self.fee_service,
                self.price_feed_node_address_provider,
                self.preferences,
            )

        return self._price_feed_service

    @property
    def fee_service(self):
        if self._fee_service is None:
            from bisq.core.provider.fee.fee_service import FeeService

            self._fee_service = FeeService(self.dao_state_service)

        return self._fee_service

    @property
    def tx_fee_estimation_service(self):
        if self._tx_fee_estimation_service is None:
            from bisq.core.btc.tx_fee_estimation_service import (
                TxFeeEstimationService,
            )

            self._tx_fee_estimation_service = TxFeeEstimationService(
                self.fee_service,
                self.btc_wallet_service,
                self.preferences,
            )

        return self._tx_fee_estimation_service

    ############################################################################### Daomodule
    @property
    def dao_setup(self):
        if self._dao_setup is None:
            from bisq.core.dao.dao_setup import DaoSetup

            self._dao_setup = DaoSetup(
                self.bsq_node_provider,
                self.accounting_node_provider,
                self.dao_state_service,
                self.cycle_service,
                self.ballot_list_service,
                self.proposal_service,
                self.proposal_list_presentation,
                self.blind_vote_list_service,
                self.my_blind_vote_list_service,
                self.vote_reveal_service,
                self.vote_result_service,
                self.missing_data_request_service,
                self.bonded_reputation_repository,
                self.bonded_roles_repository,
                self.my_reputation_list_service,
                self.my_bonded_reputation_repository,
                self.asset_service,
                self.proof_of_burn_service,
                self.dao_facade,
                self.export_json_files_service,
                self.dao_kill_switch,
                self.dao_state_monitoring_service,
                self.proposal_state_monitoring_service,
                self.blind_vote_state_monitoring_service,
                self.dao_state_snapshot_service,
                self.burning_man_accounting_service,
            )

        return self._dao_setup

    @property
    def dao_facade(self):
        if self._dao_facade is None:
            from bisq.core.dao.dao_facade import DaoFacade

            self._dao_facade = DaoFacade(
                self.my_proposal_list_service,
                self.proposal_list_presentation,
                self.proposal_service,
                self.ballot_list_service,
                self.ballot_list_presentation,
                self.dao_state_service,
                self.dao_state_monitoring_service,
                self.period_service,
                self.cycle_service,
                self.my_blind_vote_list_service,
                self.my_vote_list_service,
                self.compensation_proposal_factory,
                self.reimbursement_proposal_factory,
                self.change_param_proposal_factory,
                self.confiscate_bond_proposal_factory,
                self.role_proposal_factory,
                self.generic_proposal_factory,
                self.remove_asset_proposal_factory,
                self.bonded_roles_repository,
                self.bonded_reputation_repository,
                self.my_bonded_reputation_repository,
                self.lockup_tx_service,
                self.unlock_tx_service,
                self.dao_state_storage_service,
                self.config,
            )

        return self._dao_facade

    @property
    def dao_kill_switch(self):
        if self._dao_kill_switch is None:
            from bisq.core.dao.dao_kill_switch import DaoKillSwitch

            self._dao_kill_switch = DaoKillSwitch(self.filter_manager)

        return self._dao_kill_switch

    @property
    def block_parser(self):
        if self._block_parser is None:
            from bisq.core.dao.node.parser.block_parser import BlockParser

            self._block_parser = BlockParser(
                self.tx_parser,
                self.dao_state_service,
            )

        return self._block_parser

    @property
    def lite_node_network_service(self):
        if self._lite_node_network_service is None:
            from bisq.core.dao.node.lite.network.lite_node_network_service import (
                LiteNodeNetworkService,
            )

            self._lite_node_network_service = LiteNodeNetworkService(
                self.network_node,
                self.peer_manager,
                self.broadcaster,
                self.seed_node_repository,
            )

        return self._lite_node_network_service

    @property
    def bsq_lite_node(self):
        if self._bsq_lite_node is None:
            from bisq.core.dao.node.lite.lite_node import LiteNode

            self._bsq_lite_node = LiteNode(
                self.block_parser,
                self.dao_state_service,
                self.dao_state_snapshot_service,
                self.p2p_service,
                self.lite_node_network_service,
                self.bsq_wallet_service,
                self.wallets_setup,
                self.export_json_files_service,
            )

        return self._bsq_lite_node

    @property
    def bsq_full_node(self):
        if self._bsq_full_node is None:
            from bisq.core.dao.node.full.full_node import FullNode

            self._bsq_full_node = FullNode(
                # NOTE: not going to implement for now
            )

        return self._bsq_full_node

    @property
    def bsq_node_provider(self):
        if self._bsq_node_provider is None:
            from bisq.core.dao.node.bsq_node_provider import BsqNodeProvider

            self._bsq_node_provider = BsqNodeProvider(
                self.bsq_lite_node,
                self.bsq_full_node,
                self.preferences,
            )

        return self._bsq_node_provider

    @property
    def accounting_block_parser(self):
        if self._accounting_block_parser is None:
            from bisq.core.dao.burningman.accounting.node.full.accounting_block_parser import (
                AccountingBlockParser,
            )

            self._accounting_block_parser = AccountingBlockParser(
                self.burning_man_accounting_service,
            )

        return self._accounting_block_parser

    @property
    def accounting_lite_node_network_service(self):
        if self._accounting_lite_node_network_service is None:
            from bisq.core.dao.burningman.accounting.node.lite.network.accounting_lite_network_service import (
                AccountingLiteNodeNetworkService,
            )

            self._accounting_lite_node_network_service = (
                AccountingLiteNodeNetworkService(
                    self.network_node,
                    self.peer_manager,
                    self.broadcaster,
                    self.seed_node_repository,
                )
            )

        return self._accounting_lite_node_network_service

    @property
    def accounting_lite_node(self):
        if self._accounting_lite_node is None:
            from bisq.core.dao.burningman.accounting.node.lite.accounting_lite_node import (
                AccountingLiteNode,
            )

            self._accounting_lite_node = AccountingLiteNode(
                self.p2p_service,
                self.dao_state_service,
                self.burning_man_accounting_service,
                self.accounting_block_parser,
                self.wallets_setup,
                self.bsq_wallet_service,
                self.accounting_lite_node_network_service,
                self.preferences,
                self.config.use_dev_privilege_keys,
            )

        return self._accounting_lite_node

    @property
    def accounting_full_node(self):
        if self._accounting_full_node is None:
            from bisq.core.dao.burningman.accounting.node.full.accounting_full_node import (
                AccountingFullNode,
            )

            self._accounting_full_node = AccountingFullNode(
                # NOTE: not going to implement for now
            )

        return self._accounting_full_node

    @property
    def accounting_node_provider(self):
        if self._accounting_node_provider is None:
            from bisq.core.dao.burningman.accounting.node.accounting_node_provider import (
                AccountingNodeProvider,
            )

            self._accounting_node_provider = AccountingNodeProvider(
                self.accounting_lite_node,
                self.accounting_full_node,
                self.config.is_bm_full_node,
                self.preferences,
            )

        return self._accounting_node_provider

    @property
    def genesis_tx_info(self):
        if self._genesis_tx_info is None:
            from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo

            self._genesis_tx_info = GenesisTxInfo(
                self.config,
                self.config.genesis_tx_id,
                self.config.genesis_block_height,
                self.config.genesis_total_supply,
            )

        return self._genesis_tx_info

    @property
    def dao_state(self):
        if self._dao_state is None:
            from bisq.core.dao.state.model.dao_state import DaoState

            self._dao_state = DaoState()

        return self._dao_state

    @property
    def dao_state_service(self):
        if self._dao_state_service is None:
            from bisq.core.dao.state.dao_state_service import DaoStateService

            self._dao_state_service = DaoStateService(
                self.dao_state,
                self.genesis_tx_info,
                self.bsq_formatter,
            )

        return self._dao_state_service

    @property
    def dao_state_snapshot_service(self):
        if self._dao_state_snapshot_service is None:
            from bisq.core.dao.state.dao_state_snapshot_service import (
                DaoStateSnapshotService,
            )

            self._dao_state_snapshot_service = DaoStateSnapshotService(
                self.dao_state_service,
                self.genesis_tx_info,
                self.dao_state_storage_service,
                self.dao_state_monitoring_service,
                self.wallets_setup,
                self.bsq_wallet_service,
                self.preferences,
                self.config,
            )

        return self._dao_state_snapshot_service

    @property
    def dao_state_storage_service(self):
        if self._dao_state_storage_service is None:
            from bisq.core.dao.state.storage.dao_state_storage_service import (
                DaoStateStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._dao_state_storage_service = DaoStateStorageService(
                self.resource_data_store_service,
                self.bsq_blocks_storage_service,
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._dao_state_storage_service

    @property
    def dao_state_monitoring_service(self):
        if self._dao_state_monitoring_service is None:
            from bisq.core.dao.monitoring.dao_state_monitoring_service import (
                DaoStateMonitoringService,
            )

            self._dao_state_monitoring_service = DaoStateMonitoringService(
                self.dao_state_service,
                self.dao_state_storage_service,
                self.dao_state_network_service,
                self.genesis_tx_info,
                self.seed_node_repository,
                self.preferences,
                self.storage_dir,
                self.config.ignore_dev_msg,
            )

        return self._dao_state_monitoring_service

    @property
    def dao_state_network_service(self):
        if self._dao_state_network_service is None:
            from bisq.core.dao.monitoring.network.dao_state_network_service import (
                DaoStateNetworkService,
            )

            self._dao_state_network_service = DaoStateNetworkService(
                self.network_node,
                self.peer_manager,
                self.broadcaster,
            )

        return self._dao_state_network_service

    @property
    def proposal_state_monitoring_service(self):
        if self._proposal_state_monitoring_service is None:
            from bisq.core.dao.monitoring.proposal_state_monitoring_service import (
                ProposalStateMonitoringService,
            )

            self._proposal_state_monitoring_service = ProposalStateMonitoringService(
                self.dao_state_service,
                self.proposal_state_network_service,
                self.genesis_tx_info,
                self.period_service,
                self.proposal_service,
                self.seed_node_repository,
            )

        return self._proposal_state_monitoring_service

    @property
    def proposal_state_network_service(self):
        if self._proposal_state_network_service is None:
            from bisq.core.dao.monitoring.network.proposal_state_network_service import (
                ProposalStateNetworkService,
            )

            self._proposal_state_network_service = ProposalStateNetworkService(
                self.network_node,
                self.peer_manager,
                self.broadcaster,
            )

        return self._proposal_state_network_service

    @property
    def blind_vote_state_monitoring_service(self):
        if self._blind_vote_state_monitoring_service is None:
            from bisq.core.dao.monitoring.blind_vote_state_monitoring_service import (
                BlindVoteStateMonitoringService,
            )

            self._blind_vote_state_monitoring_service = BlindVoteStateMonitoringService(
                self.dao_state_service,
                self.blind_vote_state_network_service,
                self.genesis_tx_info,
                self.period_service,
                self.blind_vote_list_service,
                self.seed_node_repository,
            )

        return self._blind_vote_state_monitoring_service

    @property
    def blind_vote_state_network_service(self):
        if self._blind_vote_state_network_service is None:
            from bisq.core.dao.monitoring.network.blind_vote_state_network_service import (
                BlindVoteStateNetworkService,
            )

            self._blind_vote_state_network_service = BlindVoteStateNetworkService(
                self.network_node,
                self.peer_manager,
                self.broadcaster,
            )

        return self._blind_vote_state_network_service

    @property
    def unconfirmed_bsq_change_output_list_service(self):
        if self._unconfirmed_bsq_change_output_list_service is None:
            from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list_service import (
                UnconfirmedBsqChangeOutputListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._unconfirmed_bsq_change_output_list_service = (
                UnconfirmedBsqChangeOutputListService(
                    PersistenceManager(
                        self.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                        self.persistence_orchestrator,
                    )
                )
            )

        return self._unconfirmed_bsq_change_output_list_service

    @property
    def export_json_files_service(self):
        if self._export_json_files_service is None:
            from bisq.core.dao.node.explorer.export_json_file_manager import (
                ExportJsonFilesService,
            )

            self._export_json_files_service = ExportJsonFilesService(
                self.dao_state_service,
                self.storage_dir,
                self.config.dump_blockchain_data,
            )
        return self._export_json_files_service

    @property
    def cycle_service(self):
        if self._cycle_service is None:
            from bisq.core.dao.governance.period.cycle_service import CycleService

            self._cycle_service = CycleService(
                self.dao_state_service,
                self.genesis_tx_info,
            )
        return self._cycle_service

    @property
    def cycles_in_dao_state_service(self):
        if self._cycles_in_dao_state_service is None:
            from bisq.core.dao.cycles_in_dao_state_service import (
                CyclesInDaoStateService,
            )

            self._cycles_in_dao_state_service = CyclesInDaoStateService(
                self.dao_state_service,
                self.cycle_service,
            )
        return self._cycles_in_dao_state_service

    @property
    def period_service(self):
        if self._period_service is None:
            from bisq.core.dao.governance.period.period_service import PeriodService

            self._period_service = PeriodService(self.dao_state_service)
        return self._period_service

    @property
    def my_proposal_list_service(self):
        if self._my_proposal_list_service is None:
            from bisq.core.dao.governance.proposal.my_proposal_list_service import (
                MyProposalListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._my_proposal_list_service = MyProposalListService(
                self.p2p_service,
                self.dao_state_service,
                self.period_service,
                self.wallets_manager,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.key_ring.pub_key_ring,
            )

        return self._my_proposal_list_service

    @property
    def tx_parser(self):
        if self._tx_parser is None:
            from bisq.core.dao.node.parser.tx_parser import TxParser

            self._tx_parser = TxParser(
                self.period_service,
                self.dao_state_service,
            )

        return self._tx_parser

    @property
    def proposal_service(self):
        if self._proposal_service is None:
            from bisq.core.dao.governance.proposal.proposal_service import (
                ProposalService,
            )

            self._proposal_service = ProposalService(
                self.p2p_service,
                self.period_service,
                self.proposal_storage_service,
                self.temp_proposal_storage_service,
                self.append_only_data_store_service,
                self.protected_data_store_service,
                self.dao_state_service,
                self.proposal_validator_provider,
            )

        return self._proposal_service

    @property
    def proposal_list_presentation(self):
        if self._proposal_list_presentation is None:
            from bisq.core.dao.governance.proposal.proposal_list_presentation import (
                ProposalListPresentation,
            )

            self._proposal_list_presentation = ProposalListPresentation(
                self.proposal_service,
                self.dao_state_service,
                self.my_proposal_list_service,
                self.bsq_wallet_service,
                self.proposal_validator_provider,
            )

        return self._proposal_list_presentation

    @property
    def proposal_storage_service(self):
        if self._proposal_storage_service is None:
            from bisq.core.dao.governance.proposal.storage.appendonly.proposal_storage_service import (
                ProposalStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._proposal_storage_service = ProposalStorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._proposal_storage_service

    @property
    def temp_proposal_storage_service(self):
        if self._temp_proposal_storage_service is None:
            from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_storage_service import (
                TempProposalStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._temp_proposal_storage_service = TempProposalStorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._temp_proposal_storage_service

    @property
    def proposal_validator_provider(self):
        if self._proposal_validator_provider is None:
            from bisq.core.dao.governance.proposal.proposal_validator_provider import (
                ProposalValidatorProvider,
            )

            self._proposal_validator_provider = ProposalValidatorProvider(
                self.compensation_validator,
                self.confiscate_bond_validator,
                self.generic_proposal_validator,
                self.change_param_validator,
                self.reimbursement_validator,
                self.remove_asset_validator,
                self.role_validator,
            )

        return self._proposal_validator_provider

    @property
    def compensation_validator(self):
        if self._compensation_validator is None:
            from bisq.core.dao.governance.proposal.compensation.compensation_validator import (
                CompensationValidator,
            )

            self._compensation_validator = CompensationValidator(
                self.dao_state_service,
                self.period_service,
            )

        return self._compensation_validator

    @property
    def compensation_proposal_factory(self):
        if self._compensation_proposal_factory is None:
            from bisq.core.dao.governance.proposal.compensation.compensation_proposal_factory import (
                CompensationProposalFactory,
            )

            self._compensation_proposal_factory = CompensationProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.compensation_validator,
            )

        return self._compensation_proposal_factory

    @property
    def reimbursement_validator(self):
        if self._reimbursement_validator is None:
            from bisq.core.dao.governance.proposal.reimbursement.reimbursement_validator import (
                ReimbursementValidator,
            )

            self._reimbursement_validator = ReimbursementValidator(
                self.dao_state_service, self.period_service
            )

        return self._reimbursement_validator

    @property
    def reimbursement_proposal_factory(self):
        if self._reimbursement_proposal_factory is None:
            from bisq.core.dao.governance.proposal.reimbursement.reimbursement_proposal_factory import (
                ReimbursementProposalFactory,
            )

            self._reimbursement_proposal_factory = ReimbursementProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.reimbursement_validator,
            )

        return self._reimbursement_proposal_factory

    @property
    def change_param_validator(self):
        if self._change_param_validator is None:
            from bisq.core.dao.governance.proposal.param.change_param_validator import (
                ChangeParamValidator,
            )

            self._change_param_validator = ChangeParamValidator(
                self.dao_state_service,
                self.period_service,
                self.bsq_formatter,
            )

        return self._change_param_validator

    @property
    def change_param_proposal_factory(self):
        if self._change_param_proposal_factory is None:
            from bisq.core.dao.governance.proposal.param.change_param_proposal_factory import (
                ChangeParamProposalFactory,
            )

            self._change_param_proposal_factory = ChangeParamProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.change_param_validator,
            )

        return self._change_param_proposal_factory

    @property
    def role_validator(self):
        if self._role_validator is None:
            from bisq.core.dao.governance.proposal.role.role_validator import (
                RoleValidator,
            )

            self._role_validator = RoleValidator(
                self.dao_state_service, self.period_service
            )

        return self._role_validator

    @property
    def role_proposal_factory(self):
        if self._role_proposal_factory is None:
            from bisq.core.dao.governance.proposal.role.role_proposal_factory import (
                RoleProposalFactory,
            )

            self._role_proposal_factory = RoleProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.role_validator,
            )

        return self._role_proposal_factory

    @property
    def confiscate_bond_validator(self):
        if self._confiscate_bond_validator is None:
            from bisq.core.dao.governance.proposal.confiscatebond.confiscate_bond_validator import (
                ConfiscateBondValidator,
            )

            self._confiscate_bond_validator = ConfiscateBondValidator(
                self.dao_state_service, self.period_service
            )

        return self._confiscate_bond_validator

    @property
    def confiscate_bond_proposal_factory(self):
        if self._confiscate_bond_proposal_factory is None:
            from bisq.core.dao.governance.proposal.confiscatebond.confiscate_bond_proposal_factory import (
                ConfiscateBondProposalFactory,
            )

            self._confiscate_bond_proposal_factory = ConfiscateBondProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.confiscate_bond_validator,
            )

        return self._confiscate_bond_proposal_factory

    @property
    def generic_proposal_validator(self):
        if self._generic_proposal_validator is None:
            from bisq.core.dao.governance.proposal.generic.generic_proposal_validator import (
                GenericProposalValidator,
            )

            self._generic_proposal_validator = GenericProposalValidator(
                self.dao_state_service, self.period_service
            )

        return self._generic_proposal_validator

    @property
    def generic_proposal_factory(self):
        if self._generic_proposal_factory is None:
            from bisq.core.dao.governance.proposal.generic.generic_proposal_factory import (
                GenericProposalFactory,
            )

            self._generic_proposal_factory = GenericProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.generic_proposal_validator,
            )

        return self._generic_proposal_factory

    @property
    def remove_asset_validator(self):
        if self._remove_asset_validator is None:
            from bisq.core.dao.governance.proposal.remove_asset.remove_asset_validator import (
                RemoveAssetValidator,
            )

            self._remove_asset_validator = RemoveAssetValidator(
                self.dao_state_service, self.period_service
            )

        return self._remove_asset_validator

    @property
    def remove_asset_proposal_factory(self):
        if self._remove_asset_proposal_factory is None:
            from bisq.core.dao.governance.proposal.remove_asset.remove_asset_proposal_factory import (
                RemoveAssetProposalFactory,
            )

            self._remove_asset_proposal_factory = RemoveAssetProposalFactory(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
                self.remove_asset_validator,
            )

        return self._remove_asset_proposal_factory

    @property
    def ballot_list_presentation(self):
        if self._ballot_list_presentation is None:
            from bisq.core.dao.governance.ballot.ballot_list_presentation import (
                BallotListPresentation,
            )

            self._ballot_list_presentation = BallotListPresentation(
                self.ballot_list_service,
                self.period_service,
                self.dao_state_service,
                self.proposal_validator_provider,
            )

        return self._ballot_list_presentation

    @property
    def ballot_list_service(self):
        if self._ballot_list_service is None:
            from bisq.core.dao.governance.ballot.ballot_list_service import (
                BallotListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._ballot_list_service = BallotListService(
                self.proposal_service,
                self.period_service,
                self.proposal_validator_provider,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._ballot_list_service

    @property
    def my_vote_list_service(self):
        if self._my_vote_list_service is None:
            from bisq.core.dao.governance.myvote.my_vote_list_service import (
                MyVoteListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._my_vote_list_service = MyVoteListService(
                self.dao_state_service,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._my_vote_list_service

    @property
    def blind_vote_list_service(self):
        if self._blind_vote_list_service is None:
            from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
                BlindVoteListService,
            )

            self._blind_vote_list_service = BlindVoteListService(
                self.dao_state_service,
                self.p2p_service,
                self.period_service,
                self.blind_vote_storage_service,
                self.append_only_data_store_service,
                self.blind_vote_validator,
            )

        return self._blind_vote_list_service

    @property
    def blind_vote_storage_service(self):
        if self._blind_vote_storage_service is None:
            from bisq.core.dao.governance.blindvote.storage.blind_vote_storage_service import (
                BlindVoteStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._blind_vote_storage_service = BlindVoteStorageService(
                self.storage_dir,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._blind_vote_storage_service

    @property
    def blind_vote_validator(self):
        if self._blind_vote_validator is None:
            from bisq.core.dao.governance.blindvote.blind_vote_validator import (
                BlindVoteValidator,
            )

            self._blind_vote_validator = BlindVoteValidator(
                self.dao_state_service,
                self.period_service,
            )

        return self._blind_vote_validator

    @property
    def my_blind_vote_list_service(self):
        if self._my_blind_vote_list_service is None:
            from bisq.core.dao.governance.blindvote.my_blind_vote_list_service import (
                MyBlindVoteListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._my_blind_vote_list_service = MyBlindVoteListService(
                self.p2p_service,
                self.dao_state_service,
                self.period_service,
                self.wallets_manager,
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.ballot_list_service,
                self.my_vote_list_service,
                self.my_proposal_list_service,
            )

        return self._my_blind_vote_list_service

    @property
    def vote_reveal_service(self):
        if self._vote_reveal_service is None:
            from bisq.core.dao.governance.votereveal.vote_reveal_service import (
                VoteRevealService,
            )

            self._vote_reveal_service = VoteRevealService(
                self.dao_state_service,
                self.blind_vote_list_service,
                self.period_service,
                self.my_vote_list_service,
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.wallets_manager,
            )

        return self._vote_reveal_service

    @property
    def vote_result_service(self):
        if self._vote_result_service is None:
            from bisq.core.dao.governance.voteresult.vote_result_service import (
                VoteResultService,
            )

            self._vote_result_service = VoteResultService(
                self.proposal_list_presentation,
                self.dao_state_service,
                self.period_service,
                self.ballot_list_service,
                self.blind_vote_list_service,
                self.issuance_service,
                self.missing_data_request_service,
            )

        return self._vote_result_service

    @property
    def missing_data_request_service(self):
        if self._missing_data_request_service is None:
            from bisq.core.dao.governance.voteresult.missing_data_request_service import (
                MissingDataRequestService,
            )

            self._missing_data_request_service = MissingDataRequestService(
                self.republish_governance_data_handler,
                self.blind_vote_list_service,
                self.proposal_service,
                self.p2p_service,
            )

        return self._missing_data_request_service

    @property
    def issuance_service(self):
        if self._issuance_service is None:
            from bisq.core.dao.governance.voteresult.issuance.issuance_service import (
                IssuanceService,
            )

            self._issuance_service = IssuanceService(
                self.dao_state_service,
                self.period_service,
            )

        return self._issuance_service

    @property
    def republish_governance_data_handler(self):
        if self._republish_governance_data_handler is None:
            from bisq.core.dao.governance.blindvote.network.republish_governance_data_handler import (
                RepublishGovernanceDataHandler,
            )

            self._republish_governance_data_handler = RepublishGovernanceDataHandler(
                self.network_node,
                self.peer_manager,
                self.seed_node_repository,
            )

        return self._republish_governance_data_handler

    @property
    def lockup_tx_service(self):
        if self._lockup_tx_service is None:
            from bisq.core.dao.governance.bond.lockup.lockup_tx_service import (
                LockupTxService,
            )

            self._lockup_tx_service = LockupTxService(
                self.wallets_manager,
                self.bsq_wallet_service,
                self.btc_wallet_service,
            )

        return self._lockup_tx_service

    @property
    def unlock_tx_service(self):
        if self._unlock_tx_service is None:
            from bisq.core.dao.governance.bond.unlock.unlock_tx_service import (
                UnlockTxService,
            )

            self._unlock_tx_service = UnlockTxService(
                self.wallets_manager,
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.dao_state_service,
            )

        return self._unlock_tx_service

    @property
    def bonded_roles_repository(self):
        if self._bonded_roles_repository is None:
            from bisq.core.dao.governance.bond.role.bonded_roles_repository import (
                BondedRolesRepository,
            )

            self._bonded_roles_repository = BondedRolesRepository(
                self.dao_state_service,
                self.bsq_wallet_service,
            )

        return self._bonded_roles_repository

    @property
    def bonded_reputation_repository(self):
        if self._bonded_reputation_repository is None:
            from bisq.core.dao.governance.bond.reputation.bonded_reputation_repository import (
                BondedReputationRepository,
            )

            self._bonded_reputation_repository = BondedReputationRepository(
                self.dao_state_service,
                self.bsq_wallet_service,
                self.bonded_roles_repository,
            )

        return self._bonded_reputation_repository

    @property
    def my_reputation_list_service(self):
        if self._my_reputation_list_service is None:
            from bisq.core.dao.governance.bond.reputation.my_reputation_list_service import (
                MyReputationListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._my_reputation_list_service = MyReputationListService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._my_reputation_list_service

    @property
    def my_bonded_reputation_repository(self):
        if self._my_bonded_reputation_repository is None:
            from bisq.core.dao.governance.bond.reputation.my_bonded_reputation_repository import (
                MyBondedReputationRepository,
            )

            self._my_bonded_reputation_repository = MyBondedReputationRepository(
                self.dao_state_service,
                self.bsq_wallet_service,
                self.my_reputation_list_service,
            )

        return self._my_bonded_reputation_repository

    @property
    def asset_service(self):
        if self._asset_service is None:
            from bisq.core.dao.governance.asset.asset_service import AssetService

            self._asset_service = AssetService(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.wallets_manager,
                self.trade_statistics_manager,
                self.dao_state_service,
                self.bsq_formatter,
            )

        return self._asset_service

    @property
    def proof_of_burn_service(self):
        if self._proof_of_burn_service is None:
            from bisq.core.dao.governance.proofofburn.proof_of_burn_service import (
                ProofOfBurnService,
            )

            self._proof_of_burn_service = ProofOfBurnService(
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.wallets_manager,
                self.my_proof_of_burn_list_service,
                self.dao_state_service,
            )

        return self._proof_of_burn_service

    @property
    def my_proof_of_burn_list_service(self):
        if self._my_proof_of_burn_list_service is None:
            from bisq.core.dao.governance.proofofburn.my_proof_of_burn_service import (
                MyProofOfBurnListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            self._my_proof_of_burn_list_service = MyProofOfBurnListService(
                PersistenceManager(
                    self.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                    self.persistence_orchestrator,
                ),
            )

        return self._my_proof_of_burn_list_service

    @property
    def bsq_blocks_storage_service(self):
        if self._bsq_blocks_storage_service is None:
            from bisq.core.dao.state.storage.bsq_block_storage_service import (
                BsqBlocksStorageService,
            )

            self._bsq_blocks_storage_service = BsqBlocksStorageService(
                self.genesis_tx_info,
                self.persistence_proto_resolver,
                self.storage_dir,
            )

        return self._bsq_blocks_storage_service

    ############################################################################### Alert module
    @property
    def alert_manager(self):
        if self._alert_manager is None:
            from bisq.core.alert.alert_manager import AlertManager

            self._alert_manager = AlertManager(
                self.p2p_service,
                self.key_ring,
                self.user,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return self._alert_manager

    @property
    def private_notification_manager(self):
        if self._private_notification_manager is None:
            from bisq.core.alert.private_notification_manager import (
                PrivateNotificationManager,
            )

            self._private_notification_manager = PrivateNotificationManager(
                self.p2p_service,
                self.network_node,
                self.mailbox_message_service,
                self.key_ring,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return self._private_notification_manager

    ############################################################################### Filter module
    @property
    def filter_manager(self):
        if self._filter_manager is None:
            from bisq.core.filter.filter_manager import FilterManager

            self._filter_manager = FilterManager(
                self.p2p_service,
                self.key_ring,
                self.user,
                self.config,
                self.price_feed_node_address_provider,
                self.ban_filter,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return self._filter_manager
