from typing import TYPE_CHECKING, Any, List, Dict, Optional, cast
from bisq.core.monetary.volume import Volume
from bitcoinj.base.coin import Coin

from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
from bisq.core.offer.open_offer import OpenOffer
from bisq.core.trade.model.bisq_v1.trade import Trade

if TYPE_CHECKING:
    from bisq.core.trade.model.tradable import Tradable
    from bisq.core.trade.model.trade_model import TradeModel
    

# class ClosedTradableUtil:

def get_total_amount(tradable_list: List['Tradable']) -> Coin:
    return Coin.value_of(sum(amount for tradable in tradable_list 
                          for amount in tradable.get_optional_amount_as_long()))

def get_total_tx_fee(tradable_list: List['Tradable']) -> Coin:
    return Coin.value_of(sum(get_tx_fee(tradable).get_value() for tradable in tradable_list))

def get_total_volume_by_currency(tradable_list: List['Tradable']) -> Dict[str, int]:
    volume_map: Dict[str, int] = {}
    for tradable in tradable_list:
        for volume in tradable.get_optional_volume():
            if volume:
                volume = cast(Volume, volume)
                currency_code = volume.currency_code
                volume_map[currency_code] = volume_map.get(currency_code, 0) + volume.value
    return volume_map

def get_tx_fee(tradable: 'Tradable') -> Coin:
    fee = tradable.get_optional_tx_fee()
    return fee if fee else Coin.ZERO()

def is_open_offer(tradable: 'Tradable') -> bool:
    return isinstance(tradable, OpenOffer)

def is_bsq_swap_trade(tradable: 'Tradable') -> bool:
    return isinstance(tradable, BsqSwapTrade)

def is_bisq_v1_trade(tradable: 'Tradable') -> bool:
    return isinstance(tradable, Trade)

def cast_to_trade(tradable: 'Tradable') -> 'Trade':
    return tradable

def cast_to_trade_model(tradable: 'Tradable') -> 'TradeModel':
    return tradable

def cast_to_bsq_swap_trade(tradable: 'Tradable') -> 'BsqSwapTrade':
    return tradable

def cast_to_open_offer(tradable: 'Tradable') -> 'OpenOffer':
    return tradable
