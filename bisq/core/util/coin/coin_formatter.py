from abc import ABC, abstractmethod
from typing import Union
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.monetary_format import MonetaryFormat 

class CoinFormatter(ABC):
    @abstractmethod
    def format_coin(self, coin_or_value: Union['Coin', int], *, append_code: bool = False, decimal_places: int = None, decimal_aligned: bool = False, max_number_of_digits: int = None) -> str:
        # Implementation for formatting the coin
        pass

    @abstractmethod
    def format_coin_with_code(self, coin_or_value: Union['Coin', int]) -> str:
        pass

    @abstractmethod
    def get_monetary_format(self) -> MonetaryFormat:
        pass
