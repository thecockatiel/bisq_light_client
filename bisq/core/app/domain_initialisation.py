from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.core.payment.amazon_gift_card_account import AmazonGiftCardAccount
from bisq.core.payment.revolute_account import RevolutAccount
from utils.data import ObservableChangeEvent, SimplePropertyChangeEvent


if TYPE_CHECKING:
    from bisq.common.persistence.persistence_orchestrator import PersistenceOrchestrator
    from bisq.core.btc.balances import Balances
    from bisq.core.dao.governance.voteresult.vote_result_exception import (
        VoteResultException,
    )
    from bisq.core.offer.bisq_v1.trigger_price_service import TriggerPriceService
    from bisq.core.dao.dao_setup import DaoSetup
    from bisq.core.app.wallet_app_setup import WalletAppSetup
    from bisq.core.alert.private_notification_payload import PrivateNotificationPayload
    from bisq.core.offer.bsq_swap.open_bsq_swap_offer_service import (
        OpenBsqSwapOfferService,
    )
    from bisq.core.dao.state.dao_state_snapshot_service import DaoStateSnapshotService
    from bisq.core.notifications.alerts.market.market_alerts import MarketAlerts
    from bisq.core.notifications.alerts.dispute_msg_events import DisputeMsgEvents
    from bisq.core.alert.private_notification_manager import PrivateNotificationManager
    from bisq.core.notifications.alerts.price.price_alert import PriceAlert
    from bisq.core.notifications.alerts.my_offer_taken_events import MyOfferTakenEvents
    from bisq.core.notifications.alerts.trade_events import TradeEvents
    from bisq.core.notifications.mobile_notification_service import (
        MobileNotificationService,
    )
    from bisq.common.clock_watcher import ClockWatcher
    from bisq.core.dao.governance.voteresult.vote_result_service import (
        VoteResultService,
    )
    from bisq.core.account.sign.signed_witness_service import SignedWitnessService
    from bisq.core.account.witness.account_age_witness_service import (
        AccountAgeWitnessService,
    )
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.mailbox.mailbox_message_service import (
        MailboxMessageService,
    )
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.payment.trade_limits import TradeLimits
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.provider.mempool.mempool_service import MempoolService
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.support.dispute.arbitration.arbitration_manager import (
        ArbitrationManager,
    )
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import (
        ArbitratorManager,
    )
    from bisq.core.support.dispute.mediation.mediation_manager import MediationManager
    from bisq.core.support.dispute.mediation.mediator.mediator_manager import (
        MediatorManager,
    )
    from bisq.core.support.refund.refund_manager import RefundManager
    from bisq.core.support.refund.refundagent.refund_agent_manager import (
        RefundAgentManager,
    )
    from bisq.core.support.traderchat.trader_chat_manager import TraderChatManager
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import BsqSwapTradeManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.trade.txproof.xmr.xmr_tx_proof_service import XmrTxProofService
    from bisq.core.user.user import User


class DomainInitialisation:

    def __init__(
        self,
        persistence_orchestrator: "PersistenceOrchestrator",
        clock_watcher: "ClockWatcher",
        trade_limits: "TradeLimits",
        arbitration_manager: "ArbitrationManager",
        mediation_manager: "MediationManager",
        refund_manager: "RefundManager",
        trader_chat_manager: "TraderChatManager",
        trade_manager: "TradeManager",
        closed_tradable_manager: "ClosedTradableManager",
        bsq_swap_trade_manager: "BsqSwapTradeManager",
        failed_trades_manager: "FailedTradesManager",
        xmr_tx_proof_service: "XmrTxProofService",
        open_offer_manager: "OpenOfferManager",
        balances: "Balances",
        wallet_app_setup: "WalletAppSetup",
        arbitrator_manager: "ArbitratorManager",
        mediator_manager: "MediatorManager",
        refund_agent_manager: "RefundAgentManager",
        private_notification_manager: "PrivateNotificationManager",
        p2p_service: "P2PService",
        fee_service: "FeeService",
        dao_setup: "DaoSetup",
        trade_statistics_manager: "TradeStatisticsManager",
        account_age_witness_service: "AccountAgeWitnessService",
        signed_witness_service: "SignedWitnessService",
        price_feed_service: "PriceFeedService",
        filter_manager: "FilterManager",
        vote_result_service: "VoteResultService",
        mobile_notification_service: "MobileNotificationService",
        my_offer_taken_events: "MyOfferTakenEvents",
        trade_events: "TradeEvents",
        dispute_msg_events: "DisputeMsgEvents",
        price_alert: "PriceAlert",
        market_alerts: "MarketAlerts",
        user: "User",
        dao_state_snapshot_service: "DaoStateSnapshotService",
        trigger_price_service: "TriggerPriceService",
        mempool_service: "MempoolService",
        open_bsq_swap_offer_service: "OpenBsqSwapOfferService",
        mailbox_message_service: "MailboxMessageService",
    ):
        self.persistence_orchestrator = persistence_orchestrator
        self.clock_watcher = clock_watcher
        self.trade_limits = trade_limits
        self.arbitration_manager = arbitration_manager
        self.mediation_manager = mediation_manager
        self.refund_manager = refund_manager
        self.trader_chat_manager = trader_chat_manager
        self.trade_manager = trade_manager
        self.closed_tradable_manager = closed_tradable_manager
        self.bsq_swap_trade_manager = bsq_swap_trade_manager
        self.failed_trades_manager = failed_trades_manager
        self.xmr_tx_proof_service = xmr_tx_proof_service
        self.open_offer_manager = open_offer_manager
        self.balances = balances
        self.wallet_app_setup = wallet_app_setup
        self.arbitrator_manager = arbitrator_manager
        self.mediator_manager = mediator_manager
        self.refund_agent_manager = refund_agent_manager
        self.private_notification_manager = private_notification_manager
        self.p2p_service = p2p_service
        self.fee_service = fee_service
        self.dao_setup = dao_setup
        self.trade_statistics_manager = trade_statistics_manager
        self.account_age_witness_service = account_age_witness_service
        self.signed_witness_service = signed_witness_service
        self.price_feed_service = price_feed_service
        self.filter_manager = filter_manager
        self.vote_result_service = vote_result_service
        self.mobile_notification_service = mobile_notification_service
        self.my_offer_taken_events = my_offer_taken_events
        self.trade_events = trade_events
        self.dispute_msg_events = dispute_msg_events
        self.price_alert = price_alert
        self.market_alerts = market_alerts
        self.user = user
        self.dao_state_snapshot_service = dao_state_snapshot_service
        self.trigger_price_service = trigger_price_service
        self.mempool_service = mempool_service
        self.open_bsq_swap_offer_service = open_bsq_swap_offer_service
        self.mailbox_message_service = mailbox_message_service
        self._subscriptions: list[Callable[[], None]] = []

    def init_domain_services(
        self,
        rejected_tx_error_message_handler: Callable[[str], None] = None,
        display_private_notification_handler: Callable[
            ["PrivateNotificationPayload"], None
        ] = None,
        dao_error_message_handler: Callable[[str], None] = None,
        dao_warn_message_handler: Callable[[str], None] = None,
        filter_warning_handler: Callable[[str], None] = None,
        chain_not_synced_handler: Callable[[str], None] = None,
        offer_disabled_handler: Callable[[str], None] = None,
        vote_result_exception_handler: Callable = None,
        revolut_accounts_update_handler: Callable = None,
        amazon_gift_card_accounts_update_handler: Callable = None,
        resync_dao_state_from_resources_handler: Callable[[], None] = None,
    ):

        self.clock_watcher.start()

        self.persistence_orchestrator.on_all_services_initialized()

        self.trade_limits.on_all_services_initialized()

        self.trade_manager.on_all_services_initialized()
        self.arbitration_manager.on_all_services_initialized()
        self.mediation_manager.on_all_services_initialized()
        self.refund_manager.on_all_services_initialized()
        self.trader_chat_manager.on_all_services_initialized()

        self.closed_tradable_manager.on_all_services_initialized()
        self.bsq_swap_trade_manager.on_all_services_initialized()
        self.failed_trades_manager.on_all_services_initialized()
        self.xmr_tx_proof_service.on_all_services_initialized()

        self.open_offer_manager.chain_not_synced_handler = chain_not_synced_handler
        self.open_offer_manager.on_all_services_initialized()
        self.open_bsq_swap_offer_service.on_all_services_initialized()

        self.balances.on_all_services_initialized()

        self.wallet_app_setup.set_rejected_tx_error_message_handler(
            rejected_tx_error_message_handler,
            self.open_offer_manager,
            self.trade_manager,
        )

        self.arbitrator_manager.on_all_services_initialized()
        self.mediator_manager.on_all_services_initialized()
        self.refund_agent_manager.on_all_services_initialized()

        def handle_private_notif(
            e: SimplePropertyChangeEvent["PrivateNotificationPayload"],
        ):
            if display_private_notification_handler:
                display_private_notification_handler(e.new_value)

        self._subscriptions.append(
            self.private_notification_manager.private_notification_message_property.add_listener(
                handle_private_notif
            )
        )

        self.p2p_service.on_all_services_initialized()

        self.fee_service.on_all_services_initialized(self.filter_manager)

        def on_dao_error(msg: str):
            if dao_error_message_handler:
                dao_error_message_handler(msg)

        def on_dao_warn(msg: str):
            if dao_warn_message_handler:
                dao_warn_message_handler(msg)

        self.dao_setup.on_all_services_initialized(on_dao_error, on_dao_warn)

        self.dao_state_snapshot_service.resync_dao_state_from_resources_handler = (
            resync_dao_state_from_resources_handler
        )

        self.trade_statistics_manager.on_all_services_initialized()

        self.account_age_witness_service.on_all_services_initialized()
        self.signed_witness_service.on_all_services_initialized()

        self.price_feed_service.set_currency_code_on_init()

        self.filter_manager.set_filter_warning_handler(filter_warning_handler)
        self.filter_manager.on_all_services_initialized()

        def handle_vote_result_exception(
            e: ObservableChangeEvent["VoteResultException"],
        ):
            if e.added_elements and vote_result_exception_handler:
                for exc in e.added_elements:
                    vote_result_exception_handler(exc)

        self._subscriptions.append(
            self.vote_result_service.vote_result_exceptions.add_listener(
                handle_vote_result_exception
            )
        )

        self.mobile_notification_service.on_all_services_initialized()
        self.my_offer_taken_events.on_all_services_initialized()
        self.trade_events.on_all_services_initialized()
        self.dispute_msg_events.on_all_services_initialized()
        self.price_alert.on_all_services_initialized()
        self.market_alerts.on_all_services_initialized()
        self.trigger_price_service.on_all_services_initialized(offer_disabled_handler)
        self.mempool_service.on_all_services_initialized()

        self.mailbox_message_service.on_all_services_initialized()

        if revolut_accounts_update_handler:
            revolut_accounts = [
                account
                for account in self.user.payment_accounts_observable
                if isinstance(account, RevolutAccount) and account.user_name_not_set
            ]
            revolut_accounts_update_handler(revolut_accounts)

        if amazon_gift_card_accounts_update_handler:
            amazon_gift_card_accounts = [
                account
                for account in self.user.payment_accounts_observable
                if isinstance(account, AmazonGiftCardAccount)
                and account.country_not_set
            ]
            amazon_gift_card_accounts_update_handler(amazon_gift_card_accounts)

    def shut_down(self):
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()
        self.arbitration_manager.shut_down()
        self.mediation_manager.shut_down()
        self.signed_witness_service.shut_down()
        self.balances.shut_down()
        self.mailbox_message_service.shut_down()
        self.dispute_msg_events.shut_down()
        self.my_offer_taken_events.shut_down()
        self.trade_events.shut_down()
        self.market_alerts.shut_down()
        self.price_alert.shut_down()
        self.trigger_price_service.shut_down()
        self.closed_tradable_manager.shut_down()
        self.failed_trades_manager.shut_down()
        self.trade_manager.shut_down()
        self.bsq_swap_trade_manager.shut_down()
