from typing import TYPE_CHECKING, Optional, List
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from utils.data import SimpleProperty
from collections import Counter as Multiset
from typing import Optional
import copy

from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
    from bisq.core.trade.model.tradable_list import TradableList
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.model.tradable import Tradable

class BsqSwapTradeManager(PersistedDataHost):
    def __init__(self, 
                 key_ring: 'KeyRing',
                 price_feed_service: 'PriceFeedService',
                 bsq_wallet_service: 'BsqWalletService',
                 persistence_manager: 'PersistenceManager[TradableList[BsqSwapTrade]]'):
        self.key_ring = key_ring
        self.price_feed_service = price_feed_service
        self.bsq_wallet_service = bsq_wallet_service
        self.persistence_manager = persistence_manager
        self.bsq_swap_trades = TradableList['BsqSwapTrade']()
        self.confirmed_bsq_swap_node_address_cache: Optional[Multiset['NodeAddress']] = None
        # Used for listening for notifications in the UI 
        self.completed_bsq_swap_trade_property = SimpleProperty['BsqSwapTrade']()

        bsq_wallet_service.add_wallet_transactions_change_listener(
            lambda: setattr(self, 'confirmed_bsq_swap_node_address_cache', None))
        self.bsq_swap_trades.add_listener(
            lambda c: setattr(self, 'confirmed_bsq_swap_node_address_cache', None))

        self.persistence_manager.initialize(self.bsq_swap_trades, PersistenceManagerSource.PRIVATE, "BsqSwapTrades")

    def read_persisted(self, complete_handler):
        def on_persisted(persisted: 'TradableList[BsqSwapTrade]'):
            self.bsq_swap_trades.set_all(persisted.list)
            for bsq_swap_trade in self.bsq_swap_trades:
                if bsq_swap_trade.get_offer():
                    bsq_swap_trade.get_offer().price_feed_service = self.price_feed_service
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted, complete_handler)

    def on_all_services_initialized(self):
        pass

    def on_trade_completed(self, bsq_swap_trade: 'BsqSwapTrade') -> None:
        if self.find_bsq_swap_trade_by_id(bsq_swap_trade.get_id()):
            return

        if self.bsq_swap_trades.append(bsq_swap_trade):
            self._request_persistence()
            self.completed_bsq_swap_trade_property.set(bsq_swap_trade)

    def reset_completed_bsq_swap_trade(self) -> None:
        self.completed_bsq_swap_trade_property.set(None)

    def was_my_offer(self, offer: 'Offer') -> bool:
        return offer.is_my_offer(self.key_ring)

    def get_observable_list(self) -> List['BsqSwapTrade']:
        return self.bsq_swap_trades.get_observable_list()

    def get_bsq_swap_trades(self) -> List['BsqSwapTrade']:
        return copy.copy(self.get_observable_list())

    def get_tradable_list(self) -> List['Tradable']:
        return copy.copy(self.get_observable_list())

    def find_bsq_swap_trade_by_id(self, id: str) -> Optional['BsqSwapTrade']:
        return next((trade for trade in self.bsq_swap_trades if trade.get_id() == id), None)

    def get_unconfirmed_bsq_swap_trades(self) -> list:
        return [trade for trade in self.get_observable_list() if self._is_unconfirmed(trade)]

    def get_confirmed_bsq_swap_trades(self) -> list:
        return [trade for trade in self.get_observable_list() if self._is_confirmed(trade)]

    def get_confirmed_bsq_swap_node_addresses(self) -> Multiset['NodeAddress']:
        addresses = self.confirmed_bsq_swap_node_address_cache
        if addresses is None:
            self.confirmed_bsq_swap_node_address_cache = addresses = Multiset(
                trade.trading_peer_node_address
                for trade in self.bsq_swap_trades
                if self._is_confirmed(trade) and trade.trading_peer_node_address is not None
            )
        return addresses

    def _is_unconfirmed(self, bsq_swap_trade: 'BsqSwapTrade') -> bool:
        return self._matches_confidence(bsq_swap_trade, TransactionConfidenceType.PENDING)

    def _is_confirmed(self, bsq_swap_trade: 'BsqSwapTrade') -> bool:
        return self._matches_confidence(bsq_swap_trade, TransactionConfidenceType.BUILDING)

    def _matches_confidence(self, bsq_swap_trade: 'BsqSwapTrade', confidence_type: TransactionConfidenceType) -> bool:
        confidence_for_tx_id = self.bsq_wallet_service.get_confidence_for_tx_id(bsq_swap_trade.tx_id)
        return confidence_for_tx_id is not None and confidence_for_tx_id.confidence_type == confidence_type

    def _request_persistence(self) -> None:
        self.persistence_manager.request_persistence()

