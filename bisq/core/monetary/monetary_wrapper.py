from abc import ABC
from bitcoinj.base.monetary import Monetary
from bitcoinj.base.utils.monetary_format import MonetaryFormat

class MonetaryWrapper(ABC): 
    def __init__(self, monetary: Monetary) -> None:
        # Instance of Fiat or Coin
        self._monetary = monetary
        self._fiat_format = MonetaryFormat.FIAT().repeat_optional_decimals(0, 0)
        self._altcoin_format = MonetaryFormat.FIAT().repeat_optional_decimals(0, 0)

    @property
    def monetary(self):
        return self._monetary

    def is_zero(self) -> bool:
        return self._monetary.get_value() == 0

    def smallest_unit_exponent(self) -> int:
        return self._monetary.smallest_unit_exponent()

    @property
    def value(self) -> int:
        return self._monetary.get_value()

    def __eq__(self, other) -> bool:
        if not isinstance(other, MonetaryWrapper):
            return False 
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(self._monetary)