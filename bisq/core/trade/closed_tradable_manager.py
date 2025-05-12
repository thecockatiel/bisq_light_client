from collections.abc import Callable
from datetime import datetime, timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Iterator, Optional
from collections import Counter as Multiset
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.monetary.volume import Volume
from bisq.core.offer.open_offer import OpenOffer
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.trade.closed_tradable_util import cast_to_trade, cast_to_trade_model, is_bsq_swap_trade, is_open_offer
from bisq.core.trade.model.bisq_v1.trade import Trade
from bisq.core.trade.model.maker_trade import MakerTrade
from bisq.core.trade.model.tradable_list import TradableList
from bisq.core.util.average_price_util import get_average_price_tuple
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.bisq_v1.cleanup_mailbox_message_service import CleanupMailboxMessagesService
    from bisq.core.trade.bisq_v1.dump_delayed_payout_tx import DumpDelayedPayoutTx
    from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import BsqSwapTradeManager
    from bisq.core.trade.model.tradable import Tradable
    from bisq.core.trade.statistics.trade_statistics_manager import TradeStatisticsManager
    from bisq.shared.preferences.preferences import Preferences
    from bisq.core.offer.offer import Offer


# TODO: check casts later

class ClosedTradableManager(PersistedDataHost):
    """
    Manages closed trades or offers.
    BsqSwap trades are once confirmed moved in the closed trades domain as well.
    We do not manage the persistence of BsqSwap trades here but in BsqSwapTradeManager.
    """
    
    def __init__(self,
                 key_ring: 'KeyRing',
                 price_feed_service: 'PriceFeedService',
                 bsq_swap_trade_manager: 'BsqSwapTradeManager',
                 bsq_wallet_service: 'BsqWalletService',
                 preferences: 'Preferences',
                 trade_statistics_manager: 'TradeStatisticsManager',
                 persistence_manager: 'PersistenceManager[TradableList[Tradable]]',
                 cleanup_mailbox_messages_service: 'CleanupMailboxMessagesService',
                 dump_delayed_payout_tx: 'DumpDelayedPayoutTx'):
        self.logger = get_ctx_logger(__name__)
        self.key_ring = key_ring
        self.price_feed_service = price_feed_service
        self.bsq_swap_trade_manager = bsq_swap_trade_manager
        self.bsq_wallet_service = bsq_wallet_service
        self.preferences = preferences
        self.trade_statistics_manager = trade_statistics_manager
        self.cleanup_mailbox_messages_service = cleanup_mailbox_messages_service
        self.dump_delayed_payout_tx = dump_delayed_payout_tx
        self.persistence_manager = persistence_manager
        self._subscriptions: list[Callable[[], None]] = []

        self.closed_tradables = TradableList['Tradable']()
        self.closed_trade_node_address_cache: Optional[Multiset[NodeAddress]] = None

        self._subscriptions.append(self.closed_tradables.add_listener(lambda c: setattr(self, 'closed_trade_node_address_cache', None)))

        self.persistence_manager.initialize(self.closed_tradables, PersistenceManagerSource.PRIVATE, "ClosedTrades")

    def shut_down(self):
        if self.closed_trade_node_address_cache:
            self.closed_trade_node_address_cache.clear()
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

    def read_persisted(self, complete_handler: callable):
        def on_persisted(persisted: 'TradableList[Tradable]'):
            self.closed_tradables.set_all(persisted.list)
            for tradable in self.closed_tradables:
                if tradable.get_offer():
                    tradable.get_offer().price_feed_service = self.price_feed_service
            self.dump_delayed_payout_tx.maybe_dump_delayed_payout_txs(self.closed_tradables, "delayed_payout_txs_closed")
            complete_handler()
            
        self.persistence_manager.read_persisted(on_persisted, complete_handler)

    def on_all_services_initialized(self):
        self.cleanup_mailbox_messages_service.handle_trades(self.get_closed_trades())
        self.maybe_clear_sensitive_data()
        self.maybe_increase_trade_limit()

    def add(self, tradable: 'Tradable') -> None:
        if self.closed_tradables.append(tradable):
            self.maybe_clear_sensitive_data()
            self.request_persistence()

    def remove(self, tradable: 'Tradable') -> None:
        if self.closed_tradables.remove(tradable):
            self.request_persistence()

    def was_my_offer(self, offer: "Offer") -> bool:
        return offer.is_my_offer(self.key_ring)

    def get_observable_list(self):
        return self.closed_tradables.get_observable_list()

    def get_tradable_list(self):
        return list(self.get_observable_list())

    def get_closed_trades(self):
        return [e for e in self.get_observable_list() if isinstance(e, Trade)]

    def get_canceled_open_offers(self):
        return [e for e in self.get_observable_list() 
                if isinstance(e, OpenOffer) and e.state == OpenOfferState.CANCELED]

    def get_tradable_by_id(self, id: str):
        return next((e for e in self.closed_tradables if e.get_id() == id), None)

    # if user has closed trades of greater size to the default trade limit and has never customized their
    # trade limit, then set the limit to the largest amount traded previously.
    def maybe_increase_trade_limit(self):
        if not self.preferences.get_user_has_raised_trade_limit():
            closed_trades = [t for t in self.closed_tradables if isinstance(t, Trade)]
            if closed_trades:
                max_trade = max(closed_trades, key=lambda t: t.get_amount_as_long())
                if max_trade.get_amount_as_long() > self.preferences.get_user_defined_trade_limit():
                    self.logger.info(f"Increasing user trade limit to size of max completed trade: {max_trade.get_amount()}")
                    self.preferences.set_user_defined_trade_limit(max_trade.get_amount_as_long())
                    self.preferences.set_user_has_raised_trade_limit(True)

    def maybe_clear_sensitive_data(self):
        self.logger.info("checking closed trades eligibility for having sensitive data cleared")
        for trade in (t for t in self.closed_tradables if isinstance(t, Trade)):
            if self.can_trade_have_sensitive_data_cleared(trade.get_id()):
                trade.maybe_clear_sensitive_data()
        self.request_persistence()

    def can_trade_have_sensitive_data_cleared(self, trade_id: str) -> bool:
        safe_date = self.get_safe_date_for_sensitive_data_clearing()
        return any(t.get_date() < safe_date 
                  for t in self.closed_tradables 
                  if t.get_id() == trade_id)

    def get_safe_date_for_sensitive_data_clearing(self): 
        return datetime.now() - timedelta(days=self.preferences.get_clear_data_after_days())

    def get_trades_stream_with_funds_locked_in(self) -> Iterator['Trade']:
        return (t for t in self.get_closed_trades() if t.is_funds_locked_in)

    def get_closed_trade_node_addresses(self) -> Multiset:
        if self.closed_trade_node_address_cache is None:
            addresses = [t.trading_peer_node_address
                        for t in self.closed_tradables 
                        if isinstance(t, Trade)]
            self.closed_trade_node_address_cache = Multiset(
                addr for addr in addresses if addr is not None
            )
        return self.closed_trade_node_address_cache

    def get_num_past_trades(self, tradable: 'Tradable') -> int:
        if is_open_offer(tradable):
            return 0
        address_in_trade = cast_to_trade_model(tradable).trading_peer_node_address
        return (self.bsq_swap_trade_manager.get_confirmed_bsq_swap_node_addresses().get(address_in_trade, 0) +
                self.get_closed_trade_node_addresses().get(address_in_trade, 0))

    def is_currency_for_trade_fee_btc(self, tradable: 'Tradable') -> bool:
        return not self.is_bsq_trade_fee(tradable)

    def get_total_trade_fee(self, tradable_list: list['Tradable'], expect_btc_fee: bool) -> Coin:
        return Coin.value_of(sum(self.get_trade_fee(tradable, expect_btc_fee) 
                                for tradable in tradable_list))

    def get_trade_fee(self, tradable: 'Tradable', expect_btc_fee: bool) -> int:
        return self.get_btc_trade_fee(tradable) if expect_btc_fee else self.get_bsq_trade_fee(tradable)

    def get_btc_trade_fee(self, tradable: 'Tradable') -> int:
        if is_bsq_swap_trade(tradable) or self.is_bsq_trade_fee(tradable):
            return 0
        return (tradable.get_optional_maker_fee().value if self.is_maker(tradable)
                else tradable.get_optional_taker_fee().value)

    def get_bsq_trade_fee(self, tradable: 'Tradable') -> int:
        if is_bsq_swap_trade(tradable) or self.is_bsq_trade_fee(tradable):
            return (tradable.get_optional_maker_fee().value if self.is_maker(tradable)
                    else tradable.get_optional_taker_fee().value)
        return 0

    def is_bsq_trade_fee(self, tradable: 'Tradable') -> bool:
        if is_bsq_swap_trade(tradable):
            return True

        if self.is_maker(tradable):
            return not tradable.get_offer().is_currency_for_maker_fee_btc

        try:
            fee_tx_id = cast_to_trade(tradable).taker_fee_tx_id
            return self.bsq_wallet_service.get_transaction(fee_tx_id) is not None
        except:
            # this can happen when we have canceled offers in history, made using an old onion address
            return not tradable.get_offer().is_currency_for_maker_fee_btc

    def is_maker(self, tradable: 'Tradable') -> bool:
        return isinstance(tradable, MakerTrade) or tradable.get_offer().is_my_offer(self.key_ring)

    def get_bsq_volume_in_usd_with_average_price(self, amount: Coin) -> Volume:
        price_tuple = get_average_price_tuple(self.preferences, self.trade_statistics_manager, 30)
        usd_price = price_tuple[0]
        value = round(amount.value * usd_price.value / 100.0)
        return Volume(Fiat.value_of("USD", value))

    def request_persistence(self):
        self.persistence_manager.request_persistence()



