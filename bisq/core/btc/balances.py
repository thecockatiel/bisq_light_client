from datetime import timedelta
from itertools import chain
from typing import TYPE_CHECKING
from bisq.common.user_thread import UserThread
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bitcoinj.base.coin import Coin
from utils.custom_iterators import distinct_iterator, not_none_iterator
from utils.data import SimpleProperty

if TYPE_CHECKING:
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.support.refund.refund_manager import RefundManager
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.trade_manager import TradeManager


class Balances:
    
    def __init__(
        self,
        trade_manager: "TradeManager",
        btc_wallet_service: "BtcWalletService",
        open_offer_manager: "OpenOfferManager",
        closed_tradable_manager: "ClosedTradableManager",
        failed_trades_manager: "FailedTradesManager",
        refund_manager: "RefundManager",
    ):
        self._trade_manager = trade_manager
        self._btc_wallet_service = btc_wallet_service
        self._open_offer_manager = open_offer_manager
        self._closed_tradable_manager = closed_tradable_manager
        self._failed_trades_manager = failed_trades_manager
        self._refund_manager = refund_manager

        self.available_balance_property = SimpleProperty[Coin]()
        self.reserved_balance_property = SimpleProperty[Coin]()
        self.locked_balance_property = SimpleProperty[Coin]()

    @property
    def available_balance(self) -> Coin:
        return self.available_balance_property.get()
    
    @property
    def reserved_balance(self) -> Coin:
        return self.reserved_balance_property.get()
    
    @property
    def locked_balance(self) -> Coin:
        return self.locked_balance_property.get()

    def on_all_services_initialized(self):
        self._open_offer_manager.get_observable_list().add_listener(lambda *_: self.update_balance())
        self._trade_manager.get_observable_list().add_listener(lambda *_: self.update_balance())
        self._refund_manager.get_disputes_as_observable_list().add_listener(lambda *_: self.update_balance())
        self._btc_wallet_service.add_balance_listener(lambda *_: self.update_balance())
        self._btc_wallet_service.add_new_block_height_listener(lambda *_: self.update_balance())
        self.update_balance()

    def update_balance(self):
        # Need to delay a bit to get the balances correct
        UserThread.execute(lambda: [
            self.update_available_balance(),
            self.update_reserved_balance(), 
            self.update_locked_balance()
        ])

    def update_available_balance(self):
        balance_sum = sum(
            self._btc_wallet_service.get_balance_for_address(entry.get_address()).value 
            for entry in self._btc_wallet_service.get_address_entries_for_available_balance_stream()
        )
        self.available_balance_property.set(Coin.value_of(balance_sum))
        
    def update_reserved_balance(self):
        balance_sum = sum(
            self._btc_wallet_service.get_balance_for_address(address).value
            for address in distinct_iterator(
                not_none_iterator(
                    self._btc_wallet_service.get_address_entry(open_offer.get_id(), AddressEntryContext.RESERVED_FOR_TRADE)
                    for open_offer in self._open_offer_manager.get_observable_list() 
                )
            )
        )
        self.reserved_balance_property.set(Coin.value_of(balance_sum))
        
    def update_locked_balance(self):
        locked_trades = chain(
            self._closed_tradable_manager.get_trades_stream_with_funds_locked_in(),
            self._failed_trades_manager.get_trades_stream_with_funds_locked_in(),
            self._trade_manager.get_trades_stream_with_funds_locked_in()
        )
        balance_sum = sum(
            entry.coin_locked_in_multi_sig
            for entry in not_none_iterator(
                self._btc_wallet_service.get_address_entry(trade.get_id(), AddressEntryContext.MULTI_SIG)
                for trade in locked_trades
            )
        )
        self.locked_balance_property.set(Coin.value_of(balance_sum))
