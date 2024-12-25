# tried to be in the order of https://github.com/bisq-network/bisq/blob/v1.9.18/core/src/main/java/bisq/core/app/misc/ModuleForAppWithP2p.java

# TODO: fix class initializers when implemented for those who are still not done

from utils.di import DependencyProvider


class GlobalContainer:
    ############################################################################### (not listed in ModuleForAppWithP2p)
    _config = None
    _provider = None
    _corrupted_storage_file_handler = None
    _persistence_manager = None
    _bsq_formatter = None
    _removed_payloads_service = None

    _arbitrator_manager = None
    _arbitrator_service = None
    _mediator_manager = None
    _mediator_service = None
    _refund_agent_manager = None
    _refund_agent_service = None
    _arbitration_dispute_list_service = None
    _mediation_dispute_list_service = None
    _refund_dispute_list_service = None

    _mailbox_message_service = None
    _ignored_mailbox_service = None
    _bsq_swap_trade_manager = None
    _trade_statistics_manager = None
    _trade_util = None
    _wallets_manager = None
    _btc_fee_receiver_service = None
    _dump_delayed_payout_tx = None
    _create_offer_service = None
    _offer_util = None
    _cleanup_mailbox_messages_service = None

    @property
    def config(self):
        if GlobalContainer._config is None:
            from bisq.common.config.config import Config
            from utils.dir import user_data_dir

            GlobalContainer._config = Config("bisq_light_client", user_data_dir())

        return GlobalContainer._config

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
    def persistence_manager(self):
        if GlobalContainer._persistence_manager is None:
            from bisq.common.persistence.persistence_manager import PersistenceManager

            GlobalContainer._persistence_manager = PersistenceManager(
                self.config.storage_dir,
                self.persistence_proto_resolver,
                self.corrupted_storage_file_handler,
            )
        return GlobalContainer._persistence_manager

    @property
    def bsq_formatter(self):
        if GlobalContainer._bsq_formatter is None:
            from bisq.core.util.coin.bsq_formatter import BsqFormatter

            GlobalContainer._bsq_formatter = BsqFormatter()
        return GlobalContainer._bsq_formatter

    @property
    def removed_payloads_service(self):
        if GlobalContainer._removed_payloads_service is None:
            from bisq.core.network.p2p.persistence.removed_payloads_service import (
                RemovedPayloadsService,
            )

            GlobalContainer._removed_payloads_service = RemovedPayloadsService(
                self.persistence_manager
            )
        return GlobalContainer._removed_payloads_service

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

            GlobalContainer._arbitration_dispute_list_service = (
                ArbitrationDisputeListService(self.persistence_manager)
            )
        return GlobalContainer._arbitration_dispute_list_service

    @property
    def mediation_dispute_list_service(self):
        if GlobalContainer._mediation_dispute_list_service is None:
            from bisq.core.support.dispute.mediation.mediation_dispute_list_service import (
                MediationDisputeListService,
            )

            GlobalContainer._mediation_dispute_list_service = (
                MediationDisputeListService(self.persistence_manager)
            )
        return GlobalContainer._mediation_dispute_list_service

    @property
    def refund_dispute_list_service(self):
        if GlobalContainer._refund_dispute_list_service is None:
            from bisq.core.support.refund.refund_dispute_list_service import (
                RefundDisputeListService,
            )

            GlobalContainer._refund_dispute_list_service = RefundDisputeListService(
                self.persistence_manager
            )
        return GlobalContainer._refund_dispute_list_service

    @property
    def mailbox_message_service(self):
        if GlobalContainer._mailbox_message_service is None:
            from bisq.core.network.p2p.mailbox.mailbox_message_service import (
                MailboxMessageService,
            )

            GlobalContainer._mailbox_message_service = MailboxMessageService(
                self.network_node,
                self.peer_manager,
                self.p2p_data_storage,
                self.encryption_service,
                self.ignored_mailbox_service,
                self.persistence_manager,
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

            GlobalContainer._ignored_mailbox_service = IgnoredMailboxService(
                self.persistence_manager,
            )
        return GlobalContainer._ignored_mailbox_service

    @property
    def bsq_swap_trade_manager(self):
        if GlobalContainer._bsq_swap_trade_manager is None:
            from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import (
                BsqSwapTradeManager,
            )

            GlobalContainer._bsq_swap_trade_manager = BsqSwapTradeManager(
                self.key_ring,
                self.price_feed_service,
                self.bsq_wallet_service,
                self.persistence_manager,
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

            GlobalContainer._wallets_manager = WalletsManager()
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

    ############################################################################### ModuleForAppWithP2p
    _key_storage = None
    _key_ring = None
    _user = None
    _clock_watcher = None
    _network_proto_resolver = None
    _persistence_proto_resolver = None
    _preferences = None
    _bridge_address_provider = None
    _tor_setup = None

    _seed_node_repository = None
    _ban_filter = None

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

            GlobalContainer._user = User(self.persistence_manager, self.key_ring)

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

            GlobalContainer._preferences = Preferences(
                self.persistence_manager,
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
    _trade_manager = None
    _closed_tradable_manager = None
    _failed_trades_manager = None
    _account_age_witness_service = None
    _account_age_witness_storage_service = None
    _signed_witness_service = None
    _signed_witness_storage_service = None
    _referral_id_service = None

    @property
    def trade_manager(self):
        if GlobalContainer._trade_manager is None:
            from bisq.core.trade.trade_manager import TradeManager

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
                self.persistence_manager,
                self.referral_id_service,
            )
        return GlobalContainer._trade_manager

    @property
    def closed_tradable_manager(self):
        if GlobalContainer._closed_tradable_manager is None:
            from bisq.core.trade.closed_tradable_manager import ClosedTradableManager

            GlobalContainer._closed_tradable_manager = ClosedTradableManager(
                self.key_ring,
                self.price_feed_service,
                self.bsq_swap_trade_manager,
                self.bsq_wallet_service,
                self.preferences,
                self.trade_statistics_manager,
                self.persistence_manager,
                self.cleanup_mailbox_messages_service,
                self.dump_delayed_payout_tx,
            )
        return GlobalContainer._closed_tradable_manager

    @property
    def failed_trades_manager(self):
        if GlobalContainer._failed_trades_manager is None:
            from bisq.core.trade.bisq_v1.failed_trades_manager import (
                FailedTradesManager,
            )

            GlobalContainer._failed_trades_manager = FailedTradesManager(
                self.key_ring,
                self.price_feed_service,
                self.btc_wallet_service,
                self.preferences,
                self.persistence_manager,
                self.trade_util,
                self.cleanup_mailbox_messages_service,
                self.dump_delayed_payout_tx,
                self.config.allow_faulty_delayed_txs,
            )
        return GlobalContainer._failed_trades_manager

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

            GlobalContainer._account_age_witness_storage_service = (
                AccountAgeWitnessStorageService(
                    self.config.storage_dir,
                    self.persistence_manager,
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

            GlobalContainer._signed_witness_storage_service = (
                SignedWitnessStorageService(
                    self.config.storage_dir,
                    self.persistence_manager,
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
    _encryption_service = None

    @property
    def encryption_service(self):
        if GlobalContainer._encryption_service is None:
            from bisq.core.network.crypto.encryption_service import EncryptionService

            GlobalContainer._encryption_service = EncryptionService(
                self.key_ring, self.network_proto_resolver
            )
        return GlobalContainer._encryption_service

    ############################################################################### OfferModule
    _core_context = None
    _open_offer_manager = None
    _offer_book_service = None

    @property
    def core_context(self):
        if GlobalContainer._core_context is None:
            from bisq.core.api.core_context import CoreContext

            GlobalContainer._core_context = CoreContext()
        return GlobalContainer._core_context

    @property
    def open_offer_manager(self):
        if GlobalContainer._open_offer_manager is None:
            from bisq.core.offer.open_offer_manager import OpenOfferManager

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

    ############################################################################### P2PModule
    _clock = None
    _p2p_service = None
    _peer_manager = None
    _p2p_data_storage = None
    _append_only_data_store_service = None
    _protected_data_store_service = None
    _resource_data_store_service = None
    _request_data_manager = None
    _peer_exchange_manager = None
    _keep_alive_manager = None
    _broadcaster = None
    _network_node_provider = None
    _network_node = None
    _socks5_proxy_provider = None
    _http_client = None

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

            GlobalContainer._peer_manager = PeerManager(
                self.network_node,
                self.seed_node_repository,
                self.clock_watcher,
                self.persistence_manager,
                self.config.max_connections,
            )

        return GlobalContainer._peer_manager

    @property
    def p2p_data_storage(self):
        if GlobalContainer._p2p_data_storage is None:
            from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage

            GlobalContainer._p2p_data_storage = P2PDataStorage(
                self.network_node,
                self.broadcaster,
                self.append_only_data_store_service,
                self.protected_data_store_service,
                self.resource_data_store_service,
                self.persistence_manager,
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
            from bisq.core.network.p2p.persistence.resource_data_store_service import (
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
                self.config.max_connections,
                self.config.use_localhost_for_p2p,
                self.config.node_port,
                self.config.app_data_dir,
                self.config.tor_dir,
                self.config.torrc_file,
                self.config.torrc_options,
                self.config.tor_control_host,
                self.config.tor_control_port,
                self.config.tor_control_password,
                self.config.tor_use_bridges_file,
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
            from bisq.core.network.http.http_client_impl import HttpClientImpl

            GlobalContainer._http_client = HttpClientImpl(
                None, self.socks5_proxy_provider
            )

        return GlobalContainer._http_client

    ############################################################################### TODO: BitcoinModule
    _address_entry_list = None
    _wallets_setup = None
    _btc_wallet_service = None
    _bsq_wallet_service = None
    _trade_wallet_service = None
    _providers_repository = None
    _price_feed_service = None
    _fee_service = None
    _tx_fee_estimation_service = None

    @property
    def address_entry_list(self):
        if GlobalContainer._address_entry_list is None:
            from bisq.core.btc.model.address_entry_list import AddressEntryList

            GlobalContainer._address_entry_list = AddressEntryList(
                self.persistence_manager,
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
    def price_feed_service(self):
        if GlobalContainer._price_feed_service is None:
            from bisq.core.provider.price.price_feed_service import PriceFeedService

            GlobalContainer._price_feed_service = PriceFeedService(
                self.http_client,
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
    _dao_facade = None

    _genesis_tx_info = None
    _dao_state = None
    _dao_state_service = None

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

    ############################################################################### Filter module
    _filter_manager = None

    @property
    def filter_manager(self):
        if GlobalContainer._filter_manager is None:
            from bisq.core.filter.filter_manager import FilterManager

            GlobalContainer._filter_manager = FilterManager(
                self.p2p_service,
                self.key_ring,
                self.user,
                self.providers_repository,
                self.ban_filter,
                self.config.ignore_dev_msg,
                self.config.use_dev_privilege_keys,
            )
        return GlobalContainer._filter_manager

    ###############################################################################
    _pub_key_ring = None

    @property
    def pub_key_ring(self):
        if GlobalContainer._pub_key_ring is None:
            GlobalContainer._pub_key_ring = self.key_ring.pub_key_ring

        return GlobalContainer._pub_key_ring


GLOBAL_CONTAINER = GlobalContainer()
