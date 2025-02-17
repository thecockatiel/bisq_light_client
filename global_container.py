# tried to be in the order of https://github.com/bisq-network/bisq/blob/v1.9.18/core/src/main/java/bisq/core/app/misc/ModuleForAppWithP2p.java

# TODO: fix class initializers when implemented for those who are still not done
from typing import Optional
from utils.data import SimpleProperty
from utils.di import DependencyProvider

from bisq.common.config.config import Config
from utils.dir import user_data_dir

instances = {
    # To prevent infinite tmp dir creation
    "_config": Config("bisq_light_client", user_data_dir())
}


class DynamicAttributesMeta(type):
    def __getattr__(cls, name):
        return instances.get(name, None)

    def __setattr__(cls, name, value):
        instances[name] = value


class GlobalContainer(metaclass=DynamicAttributesMeta):
    ###############################################################################
    @property
    def core_context(self):
        if GlobalContainer._core_context is None:
            from bisq.core.api.core_context import CoreContext

            GlobalContainer._core_context = CoreContext()
        return GlobalContainer._core_context

    @property
    def core_api(self):
        if GlobalContainer._core_api is None:
            from bisq.core.api.core_api import CoreApi

            GlobalContainer._core_api = CoreApi(
                self.config,
                self.core_dispute_agents_service,
                self.core_help_service,
                self.core_offers_service,
                self.core_payment_accounts_service,
                self.core_price_service,
                self.core_trades_service,
                self.core_wallets_service,
                self.trade_statistics_manager,
                self.network_node,
            )
        return GlobalContainer._core_api

    @property
    def core_dispute_agents_service(self):
        if GlobalContainer._core_dispute_agents_service is None:
            from bisq.core.api.core_dipsute_agents_service import (
                CoreDisputeAgentsService,
            )

            GlobalContainer._core_dispute_agents_service = CoreDisputeAgentsService(
                self.config,
                self.key_ring,
                self.mediator_manager,
                self.refund_agent_manager,
                self.p2p_service,
            )
        return GlobalContainer._core_dispute_agents_service

    @property
    def core_help_service(self):
        if GlobalContainer._core_help_service is None:
            from bisq.core.api.core_help_service import CoreHelpService

            GlobalContainer._core_help_service = CoreHelpService()
        return GlobalContainer._core_help_service

    @property
    def core_offers_service(self):
        if GlobalContainer._core_offers_service is None:
            from bisq.core.api.core_offers_service import CoreOffersService

            GlobalContainer._core_offers_service = CoreOffersService(
                self.core_context,
                self.key_ring,
                self.core_wallets_service,
                self.create_offer_service,
                self.offer_book_service,
                self.offer_filter_service,
                self.open_offer_manager,
                self.open_bsq_swap_offer_service,
                self.offer_util,
                self.price_feed_service,
                self.user,
            )
        return GlobalContainer._core_offers_service

    @property
    def core_payment_accounts_service(self):
        if GlobalContainer._core_payment_accounts_service is None:
            from bisq.core.api.core_payment_accounts_service import (
                CorePaymentAccountsService,
            )

            GlobalContainer._core_payment_accounts_service = CorePaymentAccountsService(
                self.core_wallets_service,
                self.account_age_witness_service,
                self.user,
                self.config,
            )
        return GlobalContainer._core_payment_accounts_service

    @property
    def core_price_service(self):
        if GlobalContainer._core_price_service is None:
            from bisq.core.api.core_price_service import CorePriceService

            GlobalContainer._core_price_service = CorePriceService(
                self.preferences,
                self.price_feed_service,
                self.trade_statistics_manager,
            )
        return GlobalContainer._core_price_service

    @property
    def core_trades_service(self):
        if GlobalContainer._core_trades_service is None:
            from bisq.core.api.core_trades_service import CoreTradesService

            GlobalContainer._core_trades_service = CoreTradesService(
                self.core_context,
                self.core_wallets_service,
                self.btc_wallet_service,
                self.offer_util,
                self.bsq_swap_trade_manager,
                self.closed_tradable_manager,
                self.closed_tradable_formatter,
                self.failed_trades_manager,
                self.take_offer_model,
                self.bsq_swap_take_offer_model,
                self.trade_manager,
                self.trade_util,
                self.user,
            )
        return GlobalContainer._core_trades_service

    @property
    def core_wallets_service(self):
        if GlobalContainer._core_wallets_service is None:
            from bisq.core.api.core_wallets_service import CoreWalletsService

            GlobalContainer._core_wallets_service = CoreWalletsService(
                self.app_startup_state,
                self.core_context,
                self.balances,
                self.wallets_manager,
                self.bsq_wallet_service,
                self.bsq_transfer_service,
                self.bsq_formatter,
                self.btc_wallet_service,
                self.btc_formatter,
                self.fee_service,
                self.dao_facade,
                self.preferences,
            )
        return GlobalContainer._core_wallets_service

    @property
    def grpc_server(self):
        if GlobalContainer._grpc_server is None:
            from bisq.daemon.grpc.grpc_server import GrpcServer

            GlobalContainer._grpc_server = GrpcServer(
                self.core_context,
                self.config,
                self.grpc_dispute_agents_service,
                self.grpc_help_service,
                self.grpc_offers_service,
                self.grpc_payment_accounts_service,
                self.grpc_price_service,
                self.grpc_shutdown_service,
                self.grpc_version_service,
                self.grpc_trades_service,
                self.grpc_wallets_service,
                self.grpc_dev_commands_service,
            )
        return GlobalContainer._grpc_server

    @property
    def grpc_exception_handler(self):
        if GlobalContainer._grpc_exception_handler is None:
            from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler

            GlobalContainer._grpc_exception_handler = GrpcExceptionHandler()
        return GlobalContainer._grpc_exception_handler

    @property
    def grpc_dispute_agents_service(self):
        if GlobalContainer._grpc_dispute_agents_service is None:
            from bisq.daemon.grpc.grpc_dispute_agent_service import (
                GrpcDisputeAgentsService,
            )

            GlobalContainer._grpc_dispute_agents_service = GrpcDisputeAgentsService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_dispute_agents_service

    @property
    def grpc_help_service(self):
        if GlobalContainer._grpc_help_service is None:
            from bisq.daemon.grpc.grpc_help_service import (
                GrpcHelpService,
            )

            GlobalContainer._grpc_help_service = GrpcHelpService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_help_service

    @property
    def grpc_offers_service(self):
        if GlobalContainer._grpc_offers_service is None:
            from bisq.daemon.grpc.grpc_offers_service import GrpcOffersService

            GlobalContainer._grpc_offers_service = GrpcOffersService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_offers_service

    @property
    def grpc_payment_accounts_service(self):
        if GlobalContainer._grpc_payment_accounts_service is None:
            from bisq.daemon.grpc.grpc_payment_accounts_service import (
                GrpcPaymentAccountsService,
            )

            GlobalContainer._grpc_payment_accounts_service = GrpcPaymentAccountsService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_payment_accounts_service

    @property
    def grpc_price_service(self):
        if GlobalContainer._grpc_price_service is None:
            from bisq.daemon.grpc.grpc_price_service import GrpcPriceService

            GlobalContainer._grpc_price_service = GrpcPriceService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_price_service

    @property
    def grpc_shutdown_service(self):
        if GlobalContainer._grpc_shutdown_service is None:
            from bisq.daemon.grpc.grpc_shutdown_service import GrpcShutdownService

            GlobalContainer._grpc_shutdown_service = GrpcShutdownService(
                self.grpc_exception_handler
            )
        return GlobalContainer._grpc_shutdown_service

    @property
    def grpc_version_service(self):
        if GlobalContainer._grpc_version_service is None:
            from bisq.daemon.grpc.grpc_version_service import GrpcVersionService

            GlobalContainer._grpc_version_service = GrpcVersionService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_version_service

    @property
    def grpc_trades_service(self):
        if GlobalContainer._grpc_trades_service is None:
            from bisq.daemon.grpc.grpc_trades_service import GrpcTradesService

            GlobalContainer._grpc_trades_service = GrpcTradesService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_trades_service

    @property
    def grpc_wallets_service(self):
        if GlobalContainer._grpc_wallets_service is None:
            from bisq.daemon.grpc.grpc_wallets_service import GrpcWalletsService

            GlobalContainer._grpc_wallets_service = GrpcWalletsService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_wallets_service

    @property
    def grpc_dev_commands_service(self):
        if GlobalContainer._grpc_dev_commands_service is None:
            from bisq.daemon.grpc.grpc_dev_commands_service import (
                GrpcDevCommandsService,
            )

            GlobalContainer._grpc_dev_commands_service = GrpcDevCommandsService(
                self.core_api, self.grpc_exception_handler
            )
        return GlobalContainer._grpc_dev_commands_service

    ############################################################################### (not listed in ModuleForAppWithP2p)
    @property
    def config(self):
        if GlobalContainer._config is None:
            from bisq.common.config.config import Config
            from utils.dir import user_data_dir

            GlobalContainer._config = Config("bisq_light_client", user_data_dir())

        return GlobalContainer._config

    @property
    def bisq_setup(self):
        if GlobalContainer._bisq_setup is None:
            from bisq.core.app.bisq_setup import BisqSetup

            GlobalContainer._bisq_setup = BisqSetup(
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
        return GlobalContainer._bisq_setup

    @property
    def domain_initialisation(self):
        if GlobalContainer._domain_initialisation is None:
            from bisq.core.app.domain_initialisation import DomainInitialisation

            GlobalContainer._domain_initialisation = DomainInitialisation(
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
        return GlobalContainer._domain_initialisation

    @property
    def p2p_network_setup(self):
        if GlobalContainer._p2p_network_setup is None:
            from bisq.common.app.p2p_network_setup import P2PNetworkSetup

            GlobalContainer._p2p_network_setup = P2PNetworkSetup(
                self.price_feed_service,
                self.p2p_service,
                self.preferences,
                self.filter_manager,
            )
        return GlobalContainer._p2p_network_setup

    @property
    def provider(self):
        if GlobalContainer._provider is None:
            from bisq.core.trade.protocol.provider import Provider

            GlobalContainer._provider = Provider(
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
        return GlobalContainer._provider

    @property
    def corrupted_storage_file_handler(self):
        if GlobalContainer._corrupted_storage_file_handler is None:
            from bisq.common.file.corrupted_storage_file_handler import (
                CorruptedStorageFileHandler,
            )

            GlobalContainer._corrupted_storage_file_handler = (
                CorruptedStorageFileHandler()
            )
        return GlobalContainer._corrupted_storage_file_handler

    @property
    def btc_formatter(self):
        if GlobalContainer._btc_formatter is None:
            from bisq.core.util.coin.immutable_coin_formatter import (
                ImmutableCoinFormatter,
            )

            GlobalContainer._btc_formatter = ImmutableCoinFormatter(
                self.config.base_currency_network_parameters.get_monetary_format()
            )
        return GlobalContainer._btc_formatter

    @property
    def bsq_formatter(self):
        if GlobalContainer._bsq_formatter is None:
            from bisq.core.util.coin.bsq_formatter import BsqFormatter

            GlobalContainer._bsq_formatter = BsqFormatter(self.config)
        return GlobalContainer._bsq_formatter

    @property
    def removed_payloads_service(self):
        if GlobalContainer._removed_payloads_service is None:
            from bisq.core.network.p2p.persistence.removed_payloads_service import (
                RemovedPayloadsService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._removed_payloads_service = RemovedPayloadsService(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                )
            )
        return GlobalContainer._removed_payloads_service

    @property
    def mempool_service(self):
        if GlobalContainer._mempool_service is None:
            from bisq.core.provider.mempool.mempool_service import (
                MempoolService,
            )

            GlobalContainer._mempool_service = MempoolService(
                self.socks5_proxy_provider,
                self.config,
                self.preferences,
                self.filter_manager,
                self.dao_facade,
                self.dao_state_service,
                self.burning_man_presentation_service,
            )
        return GlobalContainer._mempool_service

    @property
    def wallet_app_setup(self):
        if GlobalContainer._wallet_app_setup is None:
            from bisq.core.app.wallet_app_setup import WalletAppSetup

            GlobalContainer._wallet_app_setup = WalletAppSetup(
                self.core_context,
                self.wallets_manager,
                self.wallets_setup,
                self.fee_service,
                self.config,
                self.preferences,
            )
        return GlobalContainer._wallet_app_setup

    @property
    def trade_limits(self):
        if GlobalContainer._trade_limits is None:
            from bisq.core.payment.trade_limits import TradeLimits

            GlobalContainer._trade_limits = TradeLimits(self.dao_state_service)
        return GlobalContainer._trade_limits

    @property
    def arbitrator_manager(self):
        if GlobalContainer._arbitrator_manager is None:
            from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import (
                ArbitratorManager,
            )

            GlobalContainer._arbitrator_manager = ArbitratorManager(
                self.key_ring,
                self.arbitrator_service,
                self.user,
                self.filter_manager,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._arbitrator_manager

    @property
    def arbitration_manager(self):
        if GlobalContainer._arbitration_manager is None:
            from bisq.core.support.dispute.arbitration.arbitration_manager import (
                ArbitrationManager,
            )

            GlobalContainer._arbitration_manager = ArbitrationManager(
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
        return GlobalContainer._arbitration_manager

    @property
    def arbitrator_service(self):
        if GlobalContainer._arbitrator_service is None:
            from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_service import (
                ArbitratorService,
            )

            GlobalContainer._arbitrator_service = ArbitratorService(
                self.p2p_service,
                self.filter_manager,
            )
        return GlobalContainer._arbitrator_service

    @property
    def mediator_manager(self):
        if GlobalContainer._mediator_manager is None:
            from bisq.core.support.dispute.mediation.mediator.mediator_manager import (
                MediatorManager,
            )

            GlobalContainer._mediator_manager = MediatorManager(
                self.key_ring,
                self.mediator_service,
                self.user,
                self.filter_manager,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._mediator_manager

    @property
    def mediation_manager(self):
        if GlobalContainer._mediation_manager is None:
            from bisq.core.support.dispute.mediation.mediation_manager import (
                MediationManager,
            )

            GlobalContainer._mediation_manager = MediationManager(
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
            )
        return GlobalContainer._mediation_manager

    @property
    def mediator_service(self):
        if GlobalContainer._mediator_service is None:
            from bisq.core.support.dispute.mediation.mediator.mediator_service import (
                MediatorService,
            )

            GlobalContainer._mediator_service = MediatorService(
                self.p2p_service,
                self.filter_manager,
            )
        return GlobalContainer._mediator_service

    @property
    def refund_manager(self):
        if GlobalContainer._refund_manager is None:
            from bisq.core.support.refund.refund_manager import (
                RefundManager,
            )

            GlobalContainer._refund_manager = RefundManager(
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
        return GlobalContainer._refund_manager

    @property
    def refund_agent_manager(self):
        if GlobalContainer._refund_agent_manager is None:
            from bisq.core.support.refund.refundagent.refund_agent_manager import (
                RefundAgentManager,
            )

            GlobalContainer._refund_agent_manager = RefundAgentManager(
                self.key_ring,
                self.refund_agent_service,
                self.user,
                self.filter_manager,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._refund_agent_manager

    @property
    def refund_agent_service(self):
        if GlobalContainer._refund_agent_service is None:
            from bisq.core.support.refund.refundagent.refund_agent_service import (
                RefundAgentService,
            )

            GlobalContainer._refund_agent_service = RefundAgentService(
                self.p2p_service,
                self.filter_manager,
            )
        return GlobalContainer._refund_agent_service

    @property
    def arbitration_dispute_list_service(self):
        if GlobalContainer._arbitration_dispute_list_service is None:
            from bisq.core.support.dispute.arbitration.arbitration_dispute_list_service import (
                ArbitrationDisputeListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._arbitration_dispute_list_service = (
                ArbitrationDisputeListService(
                    PersistenceManager(
                        self.config.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                    )
                )
            )
        return GlobalContainer._arbitration_dispute_list_service

    @property
    def mediation_dispute_list_service(self):
        if GlobalContainer._mediation_dispute_list_service is None:
            from bisq.core.support.dispute.mediation.mediation_dispute_list_service import (
                MediationDisputeListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._mediation_dispute_list_service = (
                MediationDisputeListService(
                    PersistenceManager(
                        self.config.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                    )
                )
            )
        return GlobalContainer._mediation_dispute_list_service

    @property
    def refund_dispute_list_service(self):
        if GlobalContainer._refund_dispute_list_service is None:
            from bisq.core.support.refund.refund_dispute_list_service import (
                RefundDisputeListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._refund_dispute_list_service = RefundDisputeListService(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                )
            )
        return GlobalContainer._refund_dispute_list_service

    @property
    def trader_chat_manager(self):
        if GlobalContainer._trader_chat_manager is None:
            from bisq.core.support.traderchat.trader_chat_manager import (
                TraderChatManager,
            )

            GlobalContainer._trader_chat_manager = TraderChatManager(
                self.p2p_service,
                self.wallets_setup,
                self.trade_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.pub_key_ring,
            )
        return GlobalContainer._trader_chat_manager

    @property
    def mailbox_message_service(self):
        if GlobalContainer._mailbox_message_service is None:
            from bisq.core.network.p2p.mailbox.mailbox_message_service import (
                MailboxMessageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._mailbox_message_service = MailboxMessageService(
                self.network_node,
                self.peer_manager,
                self.p2p_data_storage,
                self.encryption_service,
                self.ignored_mailbox_service,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.key_ring,
                self.clock,
                self.config.republish_mailbox_entries,
            )
        return GlobalContainer._mailbox_message_service

    @property
    def ignored_mailbox_service(self):
        if GlobalContainer._ignored_mailbox_service is None:
            from bisq.core.network.p2p.mailbox.ignored_mailbox_service import (
                IgnoredMailboxService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._ignored_mailbox_service = IgnoredMailboxService(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )
        return GlobalContainer._ignored_mailbox_service

    @property
    def bsq_swap_trade_manager(self):
        if GlobalContainer._bsq_swap_trade_manager is None:
            from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import (
                BsqSwapTradeManager,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._bsq_swap_trade_manager = BsqSwapTradeManager(
                self.key_ring,
                self.price_feed_service,
                self.bsq_wallet_service,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )
        return GlobalContainer._bsq_swap_trade_manager

    @property
    def trade_statistics_manager(self):
        if GlobalContainer._trade_statistics_manager is None:
            from bisq.core.trade.statistics.trade_statistics_manager import (
                TradeStatisticsManager,
            )

            GlobalContainer._trade_statistics_manager = TradeStatisticsManager()
        return GlobalContainer._trade_statistics_manager

    @property
    def trade_util(self):
        if GlobalContainer._trade_util is None:
            from bisq.core.trade.bisq_v1.trade_util import TradeUtil

            GlobalContainer._trade_util = TradeUtil(
                self.btc_wallet_service, self.key_ring
            )
        return GlobalContainer._trade_util

    @property
    def wallets_manager(self):
        if GlobalContainer._wallets_manager is None:
            from bisq.core.btc.wallet.wallets_manager import WalletsManager

            GlobalContainer._wallets_manager = WalletsManager(
                # TODO
                self.btc_wallet_service,
                self.trade_wallet_service,
                self.bsq_wallet_service,
                self.wallets_setup,
            )
        return GlobalContainer._wallets_manager

    @property
    def btc_fee_receiver_service(self):
        if GlobalContainer._btc_fee_receiver_service is None:
            from bisq.core.dao.burningman.btc_fee_receiver_service import (
                BtcFeeReceiverService,
            )

            GlobalContainer._btc_fee_receiver_service = BtcFeeReceiverService()
        return GlobalContainer._btc_fee_receiver_service

    @property
    def dump_delayed_payout_tx(self):
        if GlobalContainer._dump_delayed_payout_tx is None:
            from bisq.core.trade.bisq_v1.dump_delayed_payout_tx import (
                DumpDelayedPayoutTx,
            )

            GlobalContainer._dump_delayed_payout_tx = DumpDelayedPayoutTx(
                self.config.storage_dir,
                self.config.dump_delayed_payout_txs,
            )
        return GlobalContainer._dump_delayed_payout_tx

    @property
    def create_offer_service(self):
        if GlobalContainer._create_offer_service is None:
            from bisq.core.offer.bisq_v1.create_offer_service import CreateOfferService

            GlobalContainer._create_offer_service = CreateOfferService(
                self.offer_util,
                self.tx_fee_estimation_service,
                self.price_feed_service,
                self.p2p_service,
                self.pub_key_ring,
                self.user,
                self.btc_wallet_service,
            )
        return GlobalContainer._create_offer_service

    @property
    def offer_util(self):
        if GlobalContainer._offer_util is None:
            from bisq.core.offer.offer_util import OfferUtil

            GlobalContainer._offer_util = OfferUtil(
                self.account_age_witness_service,
                self.bsq_wallet_service,
                self.filter_manager,
                self.preferences,
                self.price_feed_service,
                self.p2p_service,
                self.referral_id_service,
                self.trade_statistics_manager,
            )
        return GlobalContainer._offer_util

    @property
    def cleanup_mailbox_messages_service(self):
        if GlobalContainer._cleanup_mailbox_messages_service is None:
            from bisq.core.trade.bisq_v1.cleanup_mailbox_message_service import (
                CleanupMailboxMessagesService,
            )

            GlobalContainer._cleanup_mailbox_messages_service = (
                CleanupMailboxMessagesService(
                    self.p2p_service, self.mailbox_message_service
                )
            )
        return GlobalContainer._cleanup_mailbox_messages_service

    @property
    def xmr_tx_proof_service(self):
        if GlobalContainer._xmr_tx_proof_service is None:
            from bisq.core.trade.txproof.xmr.xmr_tx_proof_service import (
                XmrTxProofService,
            )

            GlobalContainer._xmr_tx_proof_service = XmrTxProofService(
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
        return GlobalContainer._xmr_tx_proof_service

    @property
    def mobile_message_encryption(self):
        if GlobalContainer._mobile_message_encryption is None:
            from bisq.core.notifications.mobile_message_encryption import (
                MobileMessageEncryption,
            )

            GlobalContainer._mobile_message_encryption = MobileMessageEncryption()
        return GlobalContainer._mobile_message_encryption

    @property
    def mobile_notification_validator(self):
        if GlobalContainer._mobile_notification_validator is None:
            from bisq.core.notifications.mobile_notification_validator import (
                MobileNotificationValidator,
            )

            GlobalContainer._mobile_notification_validator = (
                MobileNotificationValidator()
            )
        return GlobalContainer._mobile_notification_validator

    @property
    def mobile_model(self):
        if GlobalContainer._mobile_model is None:
            from bisq.core.notifications.mobile_model import MobileModel

            GlobalContainer._mobile_model = MobileModel()
        return GlobalContainer._mobile_model

    @property
    def mobile_notification_service(self):
        if GlobalContainer._mobile_notification_service is None:
            from bisq.core.notifications.mobile_notification_service import (
                MobileNotificationService,
            )

            GlobalContainer._mobile_notification_service = MobileNotificationService(
                self.preferences,
                self.mobile_message_encryption,
                self.mobile_notification_validator,
                self.mobile_model,
                self.http_client,
                self.config.use_localhost_for_p2p,
            )
        return GlobalContainer._mobile_notification_service

    @property
    def my_offer_taken_events(self):
        if GlobalContainer._my_offer_taken_events is None:
            from bisq.core.notifications.alerts.my_offer_taken_events import (
                MyOfferTakenEvents,
            )

            GlobalContainer._my_offer_taken_events = MyOfferTakenEvents(
                self.mobile_notification_service,
                self.open_offer_manager,
            )
        return GlobalContainer._my_offer_taken_events

    @property
    def trade_events(self):
        if GlobalContainer._trade_events is None:
            from bisq.core.notifications.alerts.trade_events import (
                TradeEvents,
            )

            GlobalContainer._trade_events = TradeEvents(
                self.trade_manager,
                self.key_ring,
                self.mobile_notification_service,
            )
        return GlobalContainer._trade_events

    @property
    def dispute_msg_events(self):
        if GlobalContainer._dispute_msg_events is None:
            from bisq.core.notifications.alerts.dispute_msg_events import (
                DisputeMsgEvents,
            )

            GlobalContainer._dispute_msg_events = DisputeMsgEvents(
                self.refund_manager,
                self.mediation_manager,
                self.p2p_service,
                self.mobile_notification_service,
            )
        return GlobalContainer._dispute_msg_events

    @property
    def price_alert(self):
        if GlobalContainer._price_alert is None:
            from bisq.core.notifications.alerts.price.price_alert import PriceAlert

            GlobalContainer._price_alert = PriceAlert(
                self.price_feed_service,
                self.mobile_notification_service,
                self.user,
            )
        return GlobalContainer._price_alert

    @property
    def market_alerts(self):
        if GlobalContainer._market_alerts is None:
            from bisq.core.notifications.alerts.market.market_alerts import MarketAlerts

            GlobalContainer._market_alerts = MarketAlerts(
                self.offer_book_service,
                self.mobile_notification_service,
                self.user,
                self.price_feed_service,
                self.key_ring,
            )
        return GlobalContainer._market_alerts

    @property
    def trigger_price_service(self):
        if GlobalContainer._trigger_price_service is None:
            from bisq.core.offer.bisq_v1.trigger_price_service import (
                TriggerPriceService,
            )

            GlobalContainer._trigger_price_service = TriggerPriceService(
                self.p2p_service,
                self.open_offer_manager,
                self.mempool_service,
                self.price_feed_service,
            )
        return GlobalContainer._trigger_price_service

    @property
    def open_bsq_swap_offer_service(self):
        if GlobalContainer._open_bsq_swap_offer_service is None:
            from bisq.core.offer.bsq_swap.open_bsq_swap_offer_service import (
                OpenBsqSwapOfferService,
            )

            GlobalContainer._open_bsq_swap_offer_service = OpenBsqSwapOfferService(
                self.open_offer_manager,
                self.btc_wallet_service,
                self.bsq_wallet_service,
                self.fee_service,
                self.p2p_service,
                self.dao_facade,
                self.offer_book_service,
                self.offer_util,
                self.filter_manager,
                self.pub_key_ring,
            )
        return GlobalContainer._open_bsq_swap_offer_service

    @property
    def local_bitcoin_node(self):
        if GlobalContainer._local_bitcoin_node is None:
            from bisq.core.btc.nodes.local_bitcoin_node import (
                LocalBitcoinNode,
            )

            GlobalContainer._local_bitcoin_node = LocalBitcoinNode(self.config)
        return GlobalContainer._local_bitcoin_node

    @property
    def app_startup_state(self):
        if GlobalContainer._app_startup_state is None:
            from bisq.core.app.app_startup_state import (
                AppStartupState,
            )

            GlobalContainer._app_startup_state = AppStartupState(
                self.wallets_setup,
                self.p2p_service,
            )
        return GlobalContainer._app_startup_state

    ############################################################################### ModuleForAppWithP2p
    @property
    def key_storage(self):
        if GlobalContainer._key_storage is None:
            from bisq.common.crypto.key_storage import KeyStorage

            GlobalContainer._key_storage = KeyStorage(self.config.storage_dir)

        return GlobalContainer._key_storage

    @property
    def key_ring(self):
        if GlobalContainer._key_ring is None:
            from bisq.common.crypto.key_ring import KeyRing

            GlobalContainer._key_ring = KeyRing(self.key_storage)

        return GlobalContainer._key_ring

    @property
    def user(self):
        if GlobalContainer._user is None:
            from bisq.core.user.user import User
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._user = User(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.key_ring,
            )

        return GlobalContainer._user

    @property
    def clock_watcher(self):
        if GlobalContainer._clock_watcher is None:
            from bisq.common.clock_watcher import ClockWatcher

            GlobalContainer._clock_watcher = ClockWatcher()

        return GlobalContainer._clock_watcher

    @property
    def network_proto_resolver(self):
        if GlobalContainer._network_proto_resolver is None:
            from bisq.core.protocol.network.core_network_proto_resolver import (
                CoreNetworkProtoResolver,
            )

            GlobalContainer._network_proto_resolver = CoreNetworkProtoResolver(
                self.clock
            )

        return GlobalContainer._network_proto_resolver

    @property
    def persistence_proto_resolver(self):
        if GlobalContainer._persistence_proto_resolver is None:
            from bisq.core.protocol.persistable.core_persistence_proto_resolver import (
                CorePersistenceProtoResolver,
            )
            from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService

            class BtcWalletServiceProvider(DependencyProvider["BtcWalletService"]):
                def get(self_) -> "BtcWalletService":
                    return self.btc_wallet_service

            GlobalContainer._persistence_proto_resolver = CorePersistenceProtoResolver(
                self.clock,
                BtcWalletServiceProvider(),
                self.network_proto_resolver,
            )
        return GlobalContainer._persistence_proto_resolver

    @property
    def preferences(self):
        if GlobalContainer._preferences is None:
            from bisq.core.user.preferences import Preferences
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._preferences = Preferences(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.config,
                self.fee_service,
            )
        return GlobalContainer._preferences

    @property
    def bridge_address_provider(self):
        if GlobalContainer._bridge_address_provider is None:
            GlobalContainer._bridge_address_provider = self.preferences

        return GlobalContainer._bridge_address_provider

    @property
    def tor_setup(self):
        if GlobalContainer._tor_setup is None:
            from bisq.common.app.tor_setup import TorSetup

            GlobalContainer._tor_setup = TorSetup(self.config.tor_dir)

        return GlobalContainer._tor_setup

    @property
    def seed_node_repository(self):
        if GlobalContainer._seed_node_repository is None:
            from bisq.core.network.p2p.seed.default_seed_node_repository import (
                DefaultSeedNodeRepository,
            )

            GlobalContainer._seed_node_repository = DefaultSeedNodeRepository(
                self.config
            )

        return GlobalContainer._seed_node_repository

    @property
    def ban_filter(self):
        if GlobalContainer._ban_filter is None:
            from bisq.core.network.core_ban_filter import CoreBanFilter

            GlobalContainer._ban_filter = CoreBanFilter(self.config.ban_list)

        return GlobalContainer._ban_filter

    ###############################################################################

    _delayed_payout_tx_receiver_service = None
    _burning_man_service = None
    _burning_man_presentation_service = None

    @property
    def delayed_payout_tx_receiver_service(self):
        if GlobalContainer._delayed_payout_tx_receiver_service is None:
            from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
                DelayedPayoutTxReceiverService,
            )

            GlobalContainer._delayed_payout_tx_receiver_service = (
                DelayedPayoutTxReceiverService(
                    self.dao_state_service, self.burning_man_service
                )
            )
        return GlobalContainer._delayed_payout_tx_receiver_service

    @property
    def burning_man_service(self):
        if GlobalContainer._burning_man_service is None:
            from bisq.core.dao.burningman.burning_man_service import BurningManService

            GlobalContainer._burning_man_service = BurningManService(
                self.dao_state_service,
            )
        return GlobalContainer._burning_man_service

    @property
    def burning_man_presentation_service(self):
        if GlobalContainer._burning_man_presentation_service is None:
            from bisq.core.dao.burningman.burning_man_presentation_service import (
                BurningManPresentationService,
            )

            GlobalContainer._burning_man_presentation_service = (
                BurningManPresentationService(
                    self.burning_man_service,
                )
            )
        return GlobalContainer._burning_man_presentation_service

    ###############################################################################
    @property
    def trade_manager(self):
        if GlobalContainer._trade_manager is None:
            from bisq.core.trade.trade_manager import TradeManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._trade_manager = TradeManager(
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
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.referral_id_service,
                self.persistence_proto_resolver,
                self.dump_delayed_payout_tx,
                self.config.allow_faulty_delayed_txs,
            )
        return GlobalContainer._trade_manager

    @property
    def closed_tradable_manager(self):
        if GlobalContainer._closed_tradable_manager is None:
            from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._closed_tradable_manager = ClosedTradableManager(
                self.key_ring,
                self.price_feed_service,
                self.bsq_swap_trade_manager,
                self.bsq_wallet_service,
                self.preferences,
                self.trade_statistics_manager,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.cleanup_mailbox_messages_service,
                self.dump_delayed_payout_tx,
            )
        return GlobalContainer._closed_tradable_manager

    @property
    def closed_tradable_formatter(self):
        if GlobalContainer._closed_tradable_formatter is None:
            from bisq.core.trade.closed_tradable_formatter import (
                ClosedTradableFormatter,
            )

            GlobalContainer._closed_tradable_formatter = ClosedTradableFormatter(
                self.closed_tradable_manager,
                self.bsq_formatter,
                self.btc_formatter,
                self.bsq_wallet_service,
            )
        return GlobalContainer._closed_tradable_formatter

    @property
    def failed_trades_manager(self):
        if GlobalContainer._failed_trades_manager is None:
            from bisq.core.trade.bisq_v1.failed_trades_manager import (
                FailedTradesManager,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._failed_trades_manager = FailedTradesManager(
                self.key_ring,
                self.price_feed_service,
                self.btc_wallet_service,
                self.preferences,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.trade_util,
                self.cleanup_mailbox_messages_service,
                self.dump_delayed_payout_tx,
                self.config.allow_faulty_delayed_txs,
            )
        return GlobalContainer._failed_trades_manager

    @property
    def take_offer_model(self):
        if GlobalContainer._take_offer_model is None:
            from bisq.core.offer.bisq_v1.take_offer_model import TakeOfferModel

            GlobalContainer._take_offer_model = TakeOfferModel(
                self.account_age_witness_service,
                self.btc_wallet_service,
                self.fee_service,
                self.offer_util,
                self.price_feed_service,
            )
        return GlobalContainer._take_offer_model

    @property
    def bsq_swap_take_offer_model(self):
        if GlobalContainer._bsq_swap_take_offer_model is None:
            from bisq.core.offer.bsq_swap.bsq_swap_take_offer_model import (
                BsqSwapTakeOfferModel,
            )

            GlobalContainer._bsq_swap_take_offer_model = BsqSwapTakeOfferModel(
                self.offer_util,
                self.btc_wallet_service,
                self.bsq_wallet_service,
                self.fee_service,
                self.trade_manager,
                self.filter_manager,
            )
        return GlobalContainer._bsq_swap_take_offer_model

    @property
    def account_age_witness_service(self):
        if GlobalContainer._account_age_witness_service is None:
            from bisq.core.account.witness.account_age_witness_service import (
                AccountAgeWitnessService,
            )

            GlobalContainer._account_age_witness_service = AccountAgeWitnessService(
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
        return GlobalContainer._account_age_witness_service

    @property
    def account_age_witness_storage_service(self):
        if GlobalContainer._account_age_witness_storage_service is None:
            from bisq.core.account.witness.account_age_witness_storage_service import (
                AccountAgeWitnessStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._account_age_witness_storage_service = (
                AccountAgeWitnessStorageService(
                    self.config.storage_dir,
                    PersistenceManager(
                        self.config.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                    ),
                )
            )
        return GlobalContainer._account_age_witness_storage_service

    @property
    def signed_witness_service(self):
        if GlobalContainer._signed_witness_service is None:
            from bisq.core.account.sign.signed_witness_service import (
                SignedWitnessService,
            )

            GlobalContainer._signed_witness_service = SignedWitnessService(
                self.key_ring,
                self.p2p_service,
                self.arbitrator_manager,
                self.signed_witness_storage_service,
                self.append_only_data_store_service,
                self.user,
                self.filter_manager,
            )
        return GlobalContainer._signed_witness_service

    @property
    def signed_witness_storage_service(self):
        if GlobalContainer._signed_witness_storage_service is None:
            from bisq.core.account.sign.signed_witness_storage_service import (
                SignedWitnessStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._signed_witness_storage_service = (
                SignedWitnessStorageService(
                    self.config.storage_dir,
                    PersistenceManager(
                        self.config.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                    ),
                )
            )
        return GlobalContainer._signed_witness_storage_service

    @property
    def referral_id_service(self):
        if GlobalContainer._referral_id_service is None:
            from bisq.core.trade.statistics.referral_id_service import ReferralIdService

            GlobalContainer._referral_id_service = ReferralIdService(self.preferences)
        return GlobalContainer._referral_id_service

    ############################################################################### EncryptionServiceModule
    @property
    def encryption_service(self):
        if GlobalContainer._encryption_service is None:
            from bisq.core.network.crypto.encryption_service import EncryptionService

            GlobalContainer._encryption_service = EncryptionService(
                self.key_ring, self.network_proto_resolver
            )
        return GlobalContainer._encryption_service

    ############################################################################### OfferModule
    @property
    def open_offer_manager(self):
        if GlobalContainer._open_offer_manager is None:
            from bisq.core.offer.open_offer_manager import OpenOfferManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._open_offer_manager = OpenOfferManager(
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
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.dao_state_service,
            )
        return GlobalContainer._open_offer_manager

    @property
    def offer_book_service(self):
        if GlobalContainer._offer_book_service is None:
            from bisq.core.offer.offer_book_service import OfferBookService

            GlobalContainer._offer_book_service = OfferBookService(
                self.p2p_service,
                self.price_feed_service,
                self.filter_manager,
                self.config.storage_dir,
                self.config.dump_statistics,
            )
        return GlobalContainer._offer_book_service

    @property
    def offer_filter_service(self):
        if GlobalContainer._offer_filter_service is None:
            from bisq.core.offer.offer_filter_service import OfferFilterService

            GlobalContainer._offer_filter_service = OfferFilterService(
                self.user,
                self.preferences,
                self.filter_manager,
                self.account_age_witness_service,
            )
        return GlobalContainer._offer_filter_service

    ############################################################################### P2PModule
    @property
    def clock(self):
        if GlobalContainer._clock is None:
            from utils.clock import Clock

            GlobalContainer._clock = Clock()

        return GlobalContainer._clock

    @property
    def p2p_service(self):
        if GlobalContainer._p2p_service is None:
            from bisq.core.network.p2p.p2p_service import P2PService

            GlobalContainer._p2p_service = P2PService(
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

        return GlobalContainer._p2p_service

    @property
    def peer_manager(self):
        if GlobalContainer._peer_manager is None:
            from bisq.core.network.p2p.peers.peer_manager import PeerManager
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._peer_manager = PeerManager(
                self.network_node,
                self.seed_node_repository,
                self.clock_watcher,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.config.max_connections,
            )

        return GlobalContainer._peer_manager

    @property
    def p2p_data_storage(self):
        if GlobalContainer._p2p_data_storage is None:
            from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._p2p_data_storage = P2PDataStorage(
                self.network_node,
                self.broadcaster,
                self.append_only_data_store_service,
                self.protected_data_store_service,
                self.resource_data_store_service,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.removed_payloads_service,
                self.clock,
                self.config.MAX_SEQUENCE_NUMBER_MAP_SIZE_BEFORE_PURGE,
            )

        return GlobalContainer._p2p_data_storage

    @property
    def append_only_data_store_service(self):
        if GlobalContainer._append_only_data_store_service is None:
            from bisq.core.network.p2p.persistence.append_only_data_store_service import (
                AppendOnlyDataStoreService,
            )

            GlobalContainer._append_only_data_store_service = (
                AppendOnlyDataStoreService()
            )

        return GlobalContainer._append_only_data_store_service

    @property
    def protected_data_store_service(self):
        if GlobalContainer._protected_data_store_service is None:
            from bisq.core.network.p2p.persistence.protected_data_store_service import (
                ProtectedDataStoreService,
            )

            GlobalContainer._protected_data_store_service = ProtectedDataStoreService()

        return GlobalContainer._protected_data_store_service

    @property
    def resource_data_store_service(self):
        if GlobalContainer._resource_data_store_service is None:
            from bisq.core.network.p2p.storage.persistence.resource_data_store_service import (
                ResourceDataStoreService,
            )

            GlobalContainer._resource_data_store_service = ResourceDataStoreService()

        return GlobalContainer._resource_data_store_service

    @property
    def request_data_manager(self):
        if GlobalContainer._request_data_manager is None:
            from bisq.core.network.p2p.peers.getdata.request_data_manager import (
                RequestDataManager,
            )

            GlobalContainer._request_data_manager = RequestDataManager(
                self.network_node,
                self.seed_node_repository,
                self.p2p_data_storage,
                self.peer_manager,
            )

        return GlobalContainer._request_data_manager

    @property
    def peer_exchange_manager(self):
        if GlobalContainer._peer_exchange_manager is None:
            from bisq.core.network.p2p.peers.peerexchange.peer_exchange_manager import (
                PeerExchangeManager,
            )

            GlobalContainer._peer_exchange_manager = PeerExchangeManager(
                self.network_node,
                self.seed_node_repository,
                self.peer_manager,
            )

        return GlobalContainer._peer_exchange_manager

    @property
    def keep_alive_manager(self):
        if GlobalContainer._keep_alive_manager is None:
            from bisq.core.network.p2p.peers.keepalive.keep_alive_manager import (
                KeepAliveManager,
            )

            GlobalContainer._keep_alive_manager = KeepAliveManager(
                self.network_node,
                self.peer_manager,
            )

        return GlobalContainer._keep_alive_manager

    @property
    def broadcaster(self):
        if GlobalContainer._broadcaster is None:
            from bisq.core.network.p2p.peers.broadcaster import Broadcaster

            GlobalContainer._broadcaster = Broadcaster(
                self.network_node,
                self.peer_manager,
                self.config.max_connections,
            )

        return GlobalContainer._broadcaster

    @property
    def network_node_provider(self):
        if GlobalContainer._network_node_provider is None:
            from bisq.core.network.p2p.network_node_provider import NetworkNodeProvider

            GlobalContainer._network_node_provider = NetworkNodeProvider(
                self.network_proto_resolver,
                self.bridge_address_provider,
                self.ban_filter,
                self.config,
            )

        return GlobalContainer._network_node_provider

    @property
    def network_node(self):
        if GlobalContainer._network_node is None:
            GlobalContainer._network_node = self.network_node_provider.get()

        return GlobalContainer._network_node

    @property
    def socks5_proxy_provider(self):
        if GlobalContainer._socks5_proxy_provider is None:
            from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider

            GlobalContainer._socks5_proxy_provider = Socks5ProxyProvider(
                self.config.socks5_proxy_btc_address,
                self.config.socks5_proxy_http_address,
            )

        return GlobalContainer._socks5_proxy_provider

    @property
    def http_client(self):
        if GlobalContainer._http_client is None:
            from bisq.core.network.http.async_http_client_impl import (
                AsyncHttpClientImpl,
            )

            GlobalContainer._http_client = AsyncHttpClientImpl(
                None, self.socks5_proxy_provider
            )

        return GlobalContainer._http_client

    ############################################################################### TODO: BitcoinModule
    @property
    def address_entry_list(self):
        if GlobalContainer._address_entry_list is None:
            from bisq.core.btc.model.address_entry_list import AddressEntryList
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._address_entry_list = AddressEntryList(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._address_entry_list

    @property
    def wallets_setup(self):
        if GlobalContainer._wallets_setup is None:
            from bisq.core.btc.wallets_setup import WalletsSetup

            GlobalContainer._wallets_setup = WalletsSetup(
                self.config,
            )

        return GlobalContainer._wallets_setup

    @property
    def btc_wallet_service(self):
        if GlobalContainer._btc_wallet_service is None:
            from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService

            GlobalContainer._btc_wallet_service = BtcWalletService(
                self.wallets_setup,
                self.preferences,
                self.fee_service,
            )

        return GlobalContainer._btc_wallet_service

    @property
    def bsq_wallet_service(self):
        if GlobalContainer._bsq_wallet_service is None:
            from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService

            GlobalContainer._bsq_wallet_service = BsqWalletService(
                self.wallets_setup,
                self.preferences,
                self.fee_service,
            )

        return GlobalContainer._bsq_wallet_service

    @property
    def bsq_transfer_service(self):
        if GlobalContainer._bsq_transfer_service is None:
            from bisq.core.btc.wallet.bsq_transfer_service import BsqTransferService

            GlobalContainer._bsq_transfer_service = BsqTransferService(
                self.wallets_manager,
                self.bsq_wallet_service,
                self.btc_wallet_service,
            )

        return GlobalContainer._bsq_transfer_service

    @property
    def trade_wallet_service(self):
        if GlobalContainer._trade_wallet_service is None:
            from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService

            GlobalContainer._trade_wallet_service = TradeWalletService()

        return GlobalContainer._trade_wallet_service

    @property
    def providers_repository(self):
        if GlobalContainer._providers_repository is None:
            from bisq.core.provider.providers_repository import ProvidersRepository

            GlobalContainer._providers_repository = ProvidersRepository(
                self.config,
                self.config.providers,
                self.config.use_localhost_for_p2p,
            )

        return GlobalContainer._providers_repository

    @property
    def balances(self):
        if GlobalContainer._balances is None:
            from bisq.core.btc.balances import Balances

            GlobalContainer._balances = Balances(
                self.trade_manager,
                self.btc_wallet_service,
                self.open_offer_manager,
                self.closed_tradable_manager,
                self.failed_trades_manager,
                self.refund_manager,
            )

        return GlobalContainer._balances

    @property
    def price_feed_service(self):
        if GlobalContainer._price_feed_service is None:
            from bisq.core.provider.price.price_feed_service import PriceFeedService
            from bisq.core.provider.price_http_client import PriceHttpClient

            GlobalContainer._price_feed_service = PriceFeedService(
                PriceHttpClient(None, self.socks5_proxy_provider),
                self.fee_service,
                self.providers_repository,
                self.preferences,
            )

        return GlobalContainer._price_feed_service

    @property
    def fee_service(self):
        if GlobalContainer._fee_service is None:
            from bisq.core.provider.fee.fee_service import FeeService

            GlobalContainer._fee_service = FeeService(self.dao_state_service)

        return GlobalContainer._fee_service

    @property
    def tx_fee_estimation_service(self):
        if GlobalContainer._tx_fee_estimation_service is None:
            from bisq.core.btc.tx_fee_estimation_service import (
                TxFeeEstimationService,
            )

            GlobalContainer._tx_fee_estimation_service = TxFeeEstimationService(
                self.fee_service,
                self.btc_wallet_service,
                self.preferences,
            )

        return GlobalContainer._tx_fee_estimation_service

    ############################################################################### TODO: Daomodule
    @property
    def dao_setup(self):
        if GlobalContainer._dao_setup is None:
            from bisq.core.dao.dao_setup import DaoSetup

            GlobalContainer._dao_setup = DaoSetup(
                # TODO
            )

        return GlobalContainer._dao_setup

    @property
    def dao_facade(self):
        if GlobalContainer._dao_facade is None:
            from bisq.core.dao.dao_facade import DaoFacade

            GlobalContainer._dao_facade = DaoFacade(
                self.config,
                self.dao_state_service,
            )

        return GlobalContainer._dao_facade

    @property
    def genesis_tx_info(self):
        if GlobalContainer._genesis_tx_info is None:
            from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo

            GlobalContainer._genesis_tx_info = GenesisTxInfo(
                self.config,
                self.config.genesis_tx_id,
                self.config.genesis_block_height,
                self.config.genesis_total_supply,
            )

        return GlobalContainer._genesis_tx_info

    @property
    def dao_state(self):
        if GlobalContainer._dao_state is None:
            from bisq.core.dao.state.model.dao_state import DaoState

            GlobalContainer._dao_state = DaoState()

        return GlobalContainer._dao_state

    @property
    def dao_state_service(self):
        if GlobalContainer._dao_state_service is None:
            from bisq.core.dao.state.dao_state_service import DaoStateService

            GlobalContainer._dao_state_service = DaoStateService(
                self.dao_state, self.genesis_tx_info, self.bsq_formatter
            )

        return GlobalContainer._dao_state_service

    @property
    def dao_state_snapshot_service(self):
        if GlobalContainer._dao_state_snapshot_service is None:
            from bisq.core.dao.state.dao_state_snapshot_service import (
                DaoStateSnapshotService,
            )

            GlobalContainer._dao_state_snapshot_service = DaoStateSnapshotService(
                self.dao_state_service,
                self.genesis_tx_info,
                self.dao_state_storage_service,
                self.dao_state_monitoring_service,
                self.wallets_setup,
                self.bsq_wallet_service,
                self.preferences,
                self.config,
            )

        return GlobalContainer._dao_state_snapshot_service

    @property
    def dao_state_storage_service(self):
        if GlobalContainer._dao_state_storage_service is None:
            from bisq.core.dao.state.storage.dao_state_storage_service import (
                DaoStateStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._dao_state_storage_service = DaoStateStorageService(
                self.resource_data_store_service,
                self.bsq_blocks_storage_service,
                self.config.storage_dir,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._dao_state_storage_service

    @property
    def dao_state_monitoring_service(self):
        if GlobalContainer._dao_state_monitoring_service is None:
            from bisq.core.dao.monitoring.dao_state_monitoring_service import (
                DaoStateMonitoringService,
            )

            GlobalContainer._dao_state_monitoring_service = DaoStateMonitoringService(
                self.dao_state_service,
                self.dao_state_network_service,
                self.genesis_tx_info,
                self.seed_node_repository,
                self.preferences,
                self.config.storage_dir,
                self.config.ignore_dev_msg,
            )

        return GlobalContainer._dao_state_monitoring_service

    @property
    def dao_state_network_service(self):
        if GlobalContainer._dao_state_network_service is None:
            from bisq.core.dao.monitoring.network.dao_state_network_service import (
                DaoStateNetworkService,
            )

            GlobalContainer._dao_state_network_service = DaoStateNetworkService(
                self.network_node,
                self.peer_manager,
                self.broadcaster,
            )

        return GlobalContainer._dao_state_network_service

    @property
    def unconfirmed_bsq_change_output_list_service(self):
        if GlobalContainer._unconfirmed_bsq_change_output_list_service is None:
            from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list_service import (
                UnconfirmedBsqChangeOutputListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._unconfirmed_bsq_change_output_list_service = (
                UnconfirmedBsqChangeOutputListService(
                    PersistenceManager(
                        self.config.storage_dir,
                        self.persistence_proto_resolver,
                        self.corrupted_storage_file_handler,
                    )
                )
            )

        return GlobalContainer._unconfirmed_bsq_change_output_list_service

    @property
    def period_service(self):
        if GlobalContainer._period_service is None:
            from bisq.core.dao.governance.period.period_service import PeriodService

            GlobalContainer._period_service = PeriodService(self.dao_state_service)
        return GlobalContainer._period_service

    @property
    def my_proposal_list_service(self):
        if GlobalContainer._my_proposal_list_service is None:
            from bisq.core.dao.governance.proposal.my_proposal_list_service import (
                MyProposalListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._my_proposal_list_service = MyProposalListService(
                self.p2p_service,
                self.dao_state_service,
                self.period_service,
                self.wallets_manager,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.pub_key_ring,
            )

        return GlobalContainer._my_proposal_list_service

    @property
    def proposal_service(self):
        if GlobalContainer._proposal_service is None:
            from bisq.core.dao.governance.proposal.proposal_service import (
                ProposalService,
            )

            GlobalContainer._proposal_service = ProposalService(
                self.p2p_service,
                self.period_service,
                self.proposal_storage_service,
                self.temp_proposal_storage_service,
                self.append_only_data_store_service,
                self.protected_data_store_service,
                self.dao_state_service,
                self.proposal_validator_provider,
            )

        return GlobalContainer._proposal_service

    @property
    def proposal_list_presentation(self):
        if GlobalContainer._proposal_list_presentation is None:
            from bisq.core.dao.governance.proposal.proposal_list_presentation import (
                ProposalListPresentation,
            )

            GlobalContainer._proposal_list_presentation = ProposalListPresentation(
                self.proposal_service,
                self.dao_state_service,
                self.my_proposal_list_service,
                self.bsq_wallet_service,
                self.proposal_validator_provider,
            )

        return GlobalContainer._proposal_list_presentation

    @property
    def proposal_storage_service(self):
        if GlobalContainer._proposal_storage_service is None:
            from bisq.core.dao.governance.proposal.storage.appendonly.proposal_storage_service import (
                ProposalStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._proposal_storage_service = ProposalStorageService(
                self.config.storage_dir,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._proposal_storage_service

    @property
    def temp_proposal_storage_service(self):
        if GlobalContainer._temp_proposal_storage_service is None:
            from bisq.core.dao.governance.proposal.storage.temp.temp_proposal_storage_service import (
                TempProposalStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._temp_proposal_storage_service = TempProposalStorageService(
                self.config.storage_dir,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._temp_proposal_storage_service

    @property
    def proposal_validator_provider(self):
        if GlobalContainer._proposal_validator_provider is None:
            from bisq.core.dao.governance.proposal.proposal_validator_provider import (
                ProposalValidatorProvider,
            )
            from bisq.core.dao.governance.proposal.compensation.compensation_validator import (
                CompensationValidator,
            )
            from bisq.core.dao.governance.proposal.confiscatebond.confiscate_bond_validator import (
                ConfiscateBondValidator,
            )
            from bisq.core.dao.governance.proposal.generic.generic_proposal_validator import (
                GenericProposalValidator,
            )
            from bisq.core.dao.governance.proposal.param.change_param_validator import (
                ChangeParamValidator,
            )
            from bisq.core.dao.governance.proposal.reimbursement.reimbursement_validator import (
                ReimbursementValidator,
            )
            from bisq.core.dao.governance.proposal.remove_asset.remove_asset_validator import (
                RemoveAssetValidator,
            )
            from bisq.core.dao.governance.proposal.role.role_validator import (
                RoleValidator,
            )

            GlobalContainer._proposal_validator_provider = ProposalValidatorProvider(
                CompensationValidator(self.dao_state_service, self.period_service),
                ConfiscateBondValidator(self.dao_state_service, self.period_service),
                GenericProposalValidator(self.dao_state_service, self.period_service),
                ChangeParamValidator(
                    self.dao_state_service, self.period_service, self.bsq_formatter
                ),
                ReimbursementValidator(self.dao_state_service, self.period_service),
                RemoveAssetValidator(self.dao_state_service, self.period_service),
                RoleValidator(self.dao_state_service, self.period_service),
            )

        return GlobalContainer._proposal_validator_provider

    @property
    def ballot_list_service(self):
        if GlobalContainer._ballot_list_service is None:
            from bisq.core.dao.governance.ballot.ballot_list_service import (
                BallotListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._ballot_list_service = BallotListService(
                self.proposal_service,
                self.period_service,
                self.proposal_validator_provider,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._ballot_list_service

    @property
    def my_vote_list_service(self):
        if GlobalContainer._my_vote_list_service is None:
            from bisq.core.dao.governance.myvote.my_vote_list_service import (
                MyVoteListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._my_vote_list_service = MyVoteListService(
                self.dao_state_service,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._my_vote_list_service

    @property
    def blind_vote_list_service(self):
        if GlobalContainer._blind_vote_list_service is None:
            from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
                BlindVoteListService,
            )

            GlobalContainer._blind_vote_list_service = BlindVoteListService(
                self.dao_state_service,
                self.p2p_service,
                self.period_service,
                self.blind_vote_storage_service,
                self.append_only_data_store_service,
                self.blind_vote_validator,
            )

        return GlobalContainer._blind_vote_list_service

    @property
    def blind_vote_storage_service(self):
        if GlobalContainer._blind_vote_storage_service is None:
            from bisq.core.dao.governance.blindvote.storage.blind_vote_storage_service import (
                BlindVoteStorageService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._blind_vote_storage_service = BlindVoteStorageService(
                self.config.storage_dir,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._blind_vote_storage_service

    @property
    def blind_vote_validator(self):
        if GlobalContainer._blind_vote_validator is None:
            from bisq.core.dao.governance.blindvote.blind_vote_validator import (
                BlindVoteValidator,
            )

            GlobalContainer._blind_vote_validator = BlindVoteValidator(
                self.dao_state_service,
                self.period_service,
            )

        return GlobalContainer._blind_vote_validator

    @property
    def my_blind_vote_list_service(self):
        if GlobalContainer._my_blind_vote_list_service is None:
            from bisq.core.dao.governance.blindvote.my_blind_vote_list_service import (
                MyBlindVoteListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._my_blind_vote_list_service = MyBlindVoteListService(
                self.p2p_service,
                self.dao_state_service,
                self.period_service,
                self.wallets_manager,
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
                self.bsq_wallet_service,
                self.btc_wallet_service,
                self.ballot_list_service,
                self.my_vote_list_service,
                self.my_proposal_list_service,
            )

        return GlobalContainer._my_blind_vote_list_service

    @property
    def vote_result_service(self):
        if GlobalContainer._vote_result_service is None:
            from bisq.core.dao.governance.voteresult.vote_result_service import (
                VoteResultService,
            )

            GlobalContainer._vote_result_service = VoteResultService(
                self.proposal_list_presentation,
                self.dao_state_service,
                self.period_service,
                self.ballot_list_service,
                self.blind_vote_list_service,
                self.issuance_service,
                self.missing_data_request_service,
            )

        return GlobalContainer._vote_result_service

    @property
    def missing_data_request_service(self):
        if GlobalContainer._missing_data_request_service is None:
            from bisq.core.dao.governance.voteresult.missing_data_request_service import (
                MissingDataRequestService,
            )

            GlobalContainer._missing_data_request_service = MissingDataRequestService(
                self.republish_governance_data_handler,
                self.blind_vote_list_service,
                self.proposal_service,
                self.p2p_service,
            )

        return GlobalContainer._missing_data_request_service

    @property
    def issuance_service(self):
        if GlobalContainer._issuance_service is None:
            from bisq.core.dao.governance.voteresult.issuance.issuance_service import (
                IssuanceService,
            )

            GlobalContainer._issuance_service = IssuanceService(
                self.dao_state_service,
                self.period_service,
            )

        return GlobalContainer._issuance_service

    @property
    def republish_governance_data_handler(self):
        if GlobalContainer._republish_governance_data_handler is None:
            from bisq.core.dao.governance.blindvote.network.republish_governance_data_handler import (
                RepublishGovernanceDataHandler,
            )

            GlobalContainer._republish_governance_data_handler = (
                RepublishGovernanceDataHandler(
                    self.network_node,
                    self.peer_manager,
                    self.seed_node_repository,
                )
            )

        return GlobalContainer._republish_governance_data_handler

    @property
    def my_reputation_list_service(self):
        if GlobalContainer._my_reputation_list_service is None:
            from bisq.core.dao.governance.bond.reputation.my_reputation_list_service import (
                MyReputationListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._my_reputation_list_service = MyReputationListService(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._my_reputation_list_service

    @property
    def my_proof_of_burn_list_service(self):
        if GlobalContainer._my_proof_of_burn_list_service is None:
            from bisq.core.dao.governance.proofofburn.my_proof_of_burn_service import (
                MyProofOfBurnListService,
            )
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._my_proof_of_burn_list_service = MyProofOfBurnListService(
                PersistenceManager(
                    self.config.storage_dir,
                    self.persistence_proto_resolver,
                    self.corrupted_storage_file_handler,
                ),
            )

        return GlobalContainer._my_proof_of_burn_list_service

    @property
    def bsq_blocks_storage_service(self):
        if GlobalContainer._bsq_blocks_storage_service is None:
            from bisq.core.dao.state.storage.bsq_block_storage_service import (
                BsqBlocksStorageService,
            )

            GlobalContainer._bsq_blocks_storage_service = BsqBlocksStorageService(
                self.genesis_tx_info,
                self.persistence_proto_resolver,
                self.config.storage_dir,
            )

        return GlobalContainer._bsq_blocks_storage_service

    ############################################################################### Alert module
    @property
    def alert_manager(self):
        if GlobalContainer._alert_manager is None:
            from bisq.core.alert.alert_manager import AlertManager

            GlobalContainer._alert_manager = AlertManager(
                self.p2p_service,
                self.key_ring,
                self.user,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._alert_manager

    @property
    def private_notification_manager(self):
        if GlobalContainer._private_notification_manager is None:
            from bisq.core.alert.private_notification_manager import (
                PrivateNotificationManager,
            )

            GlobalContainer._private_notification_manager = PrivateNotificationManager(
                self.p2p_service,
                self.network_node,
                self.mailbox_message_service,
                self.key_ring,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._private_notification_manager

    ############################################################################### Filter module
    @property
    def filter_manager(self):
        if GlobalContainer._filter_manager is None:
            from bisq.core.filter.filter_manager import FilterManager

            GlobalContainer._filter_manager = FilterManager(
                self.p2p_service,
                self.key_ring,
                self.user,
                self.config,
                self.providers_repository,
                self.ban_filter,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._filter_manager

    ###############################################################################
    @property
    def pub_key_ring(self):
        if GlobalContainer._pub_key_ring is None:
            GlobalContainer._pub_key_ring = self.key_ring.pub_key_ring

        return GlobalContainer._pub_key_ring


GLOBAL_CONTAINER = SimpleProperty[Optional[GlobalContainer]]()
# TODO: init with None for catching bugs later.
# this is done for convenience during dev
GLOBAL_CONTAINER.value = GlobalContainer()


def set_global_container(container: GlobalContainer):
    global GLOBAL_CONTAINER
    GLOBAL_CONTAINER.set(container)
