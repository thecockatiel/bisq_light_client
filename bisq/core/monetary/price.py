from functools import total_ordering
from typing import TYPE_CHECKING

from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.currency_util import is_fiat_currency
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.altcoin_exchange_rate import AltcoinExchangeRate
from bisq.core.monetary.monetary_wrapper import MonetaryWrapper
from bisq.core.util.parsing_utils import ParsingUtils
from bitcoinj.base.coin import Coin
from bitcoinj.base.monetary import Monetary
from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.util.exchange_rate import ExchangeRate

if TYPE_CHECKING:
    from bisq.core.monetary.volume import Volume

@total_ordering
class Price(MonetaryWrapper):
    """
    Bitcoin price value with variable precision.
    
    We wrap an object implementing the Monetary interface from bitcoinj. We respect the
    number of decimal digits of precision specified in the smallest_unit_exponent(), defined in
    those classes, like Fiat or Altcoin.
    """

    def __init__(self, monetary: Monetary) -> None:
        super().__init__(monetary)
        
        
    @staticmethod
    def parse(currency_code: str, input_str: str) -> 'Price':
        """
        Parse the Bitcoin Price given a currency code and input value.
        
        Args:
            currency_code: The currency code to parse, e.g "USD" or "LTC"
            input_value: The input value to parse as a String, e.g "2.54" or "-0.0001"
            
        Returns:
            Price: The parsed Price object
        """
        cleaned = ParsingUtils.convert_chars_for_number(input_str)
        if is_fiat_currency(currency_code):
            return Price(Fiat.parse_fiat(currency_code, cleaned))
        else:
            return Price(Altcoin.parse_altcoin(currency_code, cleaned))
        
    @staticmethod
    def value_of(currency_code: str, value: int):
        if is_fiat_currency(currency_code):
            return Price(Fiat.value_of(currency_code, value))
        else:
            return Price(Altcoin.value_of(currency_code, value))
        
    def get_volume_by_amount(self, amount: Coin):
        from bisq.core.monetary.volume import Volume
        if isinstance(self.monetary, Fiat):
            return Volume(self.coin_to_fiat(ExchangeRate(fiat=self.monetary), amount))
        elif isinstance(self.monetary, Altcoin):
            return Volume(AltcoinExchangeRate(altcoin=self.monetary).coin_to_altcoin(amount))
        else:
            raise IllegalStateException("Monetary must be either of type Fiat or Altcoin")
    
    @staticmethod
    def coin_to_fiat(rate: ExchangeRate, convert_coin: Coin) -> Fiat:
        # Short circuit BigInteger logic in ExchangeRate.coinToFiat in a common case where long arithmetic won't overflow.
        # NOTE: the above comment was from original bisq, but to have the same behavior, we do the same check here.
        if (int(convert_coin.value) == convert_coin.value and int(rate.fiat.value) == rate.fiat.value):
            converted = convert_coin.value * rate.fiat.value / rate.coin.value
            return Fiat.value_of(rate.fiat.currency_code, converted)
            
        return rate.coin_to_fiat(convert_coin)
    
    def get_amount_by_volume(self, volume: "Volume"):
        monetary = volume.monetary
        if isinstance(monetary, Fiat) and isinstance(self.monetary, Fiat):
            return self.fiat_to_coin(ExchangeRate(fiat=monetary), monetary.value)
        
    @staticmethod
    def fiat_to_coin(rate: ExchangeRate, convert_fiat: Fiat) -> Coin:
        # Short circuit BigInteger logic in ExchangeRate.coinToFiat in a common case where long arithmetic won't overflow.
        # NOTE: the above comment was from original bisq, but to have the same behavior, we do the same check here.
        if (int(convert_fiat.value) == convert_fiat.value and int(rate.coin.value) == rate.coin.value):
            converted = convert_fiat.value * rate.fiat.value / rate.coin.value
            return Coin.value_of(converted)
            
        return rate.fiat_to_coin(convert_fiat)
    
    def get_currency_code(self) -> str:
        return self.monetary.currency_code # either of altcoin or fiat have currency_code
    
    def get_value(self):
        return self.monetary.get_value()
    
    def __eq__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return (self.get_currency_code() == other.get_currency_code() and
                self.get_value() == other.get_value())
    
    def __lt__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        if self.get_currency_code() != other.get_currency_code():
            return self.get_currency_code() < other.get_currency_code()
        return self.get_value() < other.get_value()
    
    def is_positive(self) -> bool:
        return self.monetary.is_positive()
    
    def subtract(self, other: 'Price') -> 'Price':
        return Price(self.monetary.subtract(other.monetary))
    
    def to_friendly_string(self) -> str:
        if isinstance(self.monetary, Altcoin):
            return f"{self.monetary.to_friendly_string()}/BTC"
        return f"{self.monetary.to_friendly_string().replace(self.monetary.currency_code, '')}BTC/{self.monetary.currency_code}"
    
    def to_plain_string(self) -> str:
        return self.monetary.to_plain_string()
    
    def __str__(self) -> str:
        return self.to_plain_string()

