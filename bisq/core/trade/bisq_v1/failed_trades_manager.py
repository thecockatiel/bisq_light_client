from collections.abc import Callable
from datetime import timedelta, datetime
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Iterator, Optional, List
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.model.tradable_list import TradableList

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.bisq_v1.cleanup_mailbox_message_service import (
        CleanupMailboxMessagesService,
    )
    from bisq.core.trade.bisq_v1.dump_delayed_payout_tx import DumpDelayedPayoutTx
    from bisq.core.trade.bisq_v1.trade_util import TradeUtil
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.user.preferences import Preferences
    from bisq.core.offer.offer import Offer
    from bisq.core.btc.model.address_entry import AddressEntry



class FailedTradesManager(PersistedDataHost):
    def __init__(
        self,
        key_ring: "KeyRing",
        price_feed_service: "PriceFeedService",
        btc_wallet_service: "BtcWalletService",
        preferences: "Preferences",
        persistence_manager: "PersistenceManager[TradableList[Trade]]",
        trade_util: "TradeUtil",
        cleanup_mailbox_messages_service: "CleanupMailboxMessagesService",
        dump_delayed_payout_tx: "DumpDelayedPayoutTx",
        allow_faulty_delayed_txs: bool,
    ):
        self.logger = get_ctx_logger(__name__)
        self.failed_trades = TradableList["Trade"]()
        self.key_ring = key_ring
        self.price_feed_service = price_feed_service
        self.btc_wallet_service = btc_wallet_service
        self.preferences = preferences
        self.cleanup_mailbox_messages_service = cleanup_mailbox_messages_service
        self.dump_delayed_payout_tx = dump_delayed_payout_tx
        self.persistence_manager = persistence_manager
        self.trade_util = trade_util
        self.allow_faulty_delayed_txs = allow_faulty_delayed_txs
        self.unfail_trade_callback: Optional[Callable[["Trade"], bool]] = None

        self.persistence_manager.initialize(
            self.failed_trades, PersistenceManagerSource.PRIVATE, "FailedTrades"
        )

    def read_persisted(self, complete_handler: Callable[[], None]):
        def on_persisted(persisted: "TradableList[Trade]"):
            self.failed_trades.set_all(persisted.list)
            for trade in self.failed_trades:
                if trade.get_offer():
                    trade.get_offer().price_feed_service = self.price_feed_service
            self.dump_delayed_payout_tx.maybe_dump_delayed_payout_txs(
                self.failed_trades, "delayed_payout_txs_failed"
            )
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted, complete_handler)

    def on_all_services_initialized(self):
        self.cleanup_mailbox_messages_service.handle_trades(self.failed_trades.list)
        self.maybe_clear_sensitive_data()

    def add(self, trade: "Trade"):
        if self.failed_trades.append(trade):
            self.maybe_clear_sensitive_data()
            self.request_persistence()

    def remove_trade(self, trade: "Trade"):
        if self.failed_trades.remove(trade):
            self.request_persistence()

    def was_my_offer(self, offer: "Offer"):
        return offer.is_my_offer(self.key_ring)

    def get_observable_list(self):
        return self.failed_trades.get_observable_list()

    def get_trades(self):
        return list(self.get_observable_list())

    def get_trade_by_id(self, id: str) -> Optional["Trade"]:
        return next(
            (trade for trade in self.failed_trades if trade.get_id() == id), None
        )

    def get_trades_stream_with_funds_locked_in(self) -> Iterator['Trade']:
        return filter(lambda trade: trade.is_funds_locked_in, self.failed_trades)

    def unfail_trade(self, trade: "Trade"):
        if self.unfail_trade_callback is None:
            return

        if self.unfail_trade_callback(trade):
            self.logger.info(f"Unfailing trade {trade.get_id()}")
            if self.failed_trades.remove(trade):
                self.request_persistence()

    def check_unfail(self, trade: "Trade") -> str:
        addresses = self.trade_util.get_trade_addresses(trade)
        if addresses is None:
            return "Addresses not found"
        blocking_trade_ids = self.get_blocking_trade_ids(trade)
        return ",".join(blocking_trade_ids) if blocking_trade_ids else ""

    def get_blocking_trade_ids(self, trade: "Trade") -> Optional[List[str]]:
        trade_addresses = self.trade_util.get_trade_addresses(trade)
        if trade_addresses is None:
            return None

        def is_being_used_for_other_trade(address_entry: "AddressEntry") -> bool:
            if address_entry.context == AddressEntryContext.AVAILABLE:
                return False
            address = address_entry.get_address_string()
            return address is not None and (
                address == trade_addresses[0] or address == trade_addresses[1]
            )

        blocking_trade_ids = []
        for (
            address_entry
        ) in self.btc_wallet_service.get_address_entry_list_as_immutable_list():
            if is_being_used_for_other_trade(address_entry):
                offer_id = address_entry.offer_id
                # JAVA TODO Be certain 'List<String> blockingTrades' should NOT be populated
                #  with the trade parameter's tradeId.  The 'var address_entry' will
                #  always be found in the 'var trade_addresses' tuple, so check
                #  offerId != trade.getId() to avoid the bug being fixed by the next if
                #  statement (if it was a bug).
                if offer_id != trade.get_id() and offer_id not in blocking_trade_ids:
                    blocking_trade_ids.append(offer_id)

        return blocking_trade_ids if blocking_trade_ids else None

    def has_deposit_tx(self, failed_trade: "Trade") -> bool:
        if failed_trade.deposit_tx is None:
            self.logger.warning(f"Failed trade {failed_trade.get_id()} has no deposit tx.")
            return False
        return True

    def has_delayed_payout_tx_bytes(self, failed_trade: "Trade") -> bool:
        if failed_trade.delayed_payout_tx_bytes is not None:
            return True
        self.logger.warning(
            f"Failed trade {failed_trade.get_id()} has no delayedPayoutTxBytes."
        )
        return self.allow_faulty_delayed_txs

    def request_persistence(self):
        self.persistence_manager.request_persistence()

    def maybe_clear_sensitive_data(self):
        self.logger.info(
            "checking failed trades eligibility for having sensitive data cleared"
        )
        eligible_trades = [
            trade
            for trade in self.failed_trades
            if self.can_trade_have_sensitive_data_cleared(trade.get_id())
        ]
        for trade in eligible_trades:
            trade.maybe_clear_sensitive_data()
        self.request_persistence()

    def can_trade_have_sensitive_data_cleared(self, trade_id: str) -> bool:
        safe_date = self.get_safe_date_for_sensitive_data_clearing()
        return any(
            trade.get_id() == trade_id and trade.get_date() < safe_date
            for trade in self.failed_trades
        )

    def get_safe_date_for_sensitive_data_clearing(self):
        return datetime.now() - timedelta(
            days=self.preferences.get_clear_data_after_days()
        )
