
# Cloned from ExchangeRate. Use Altcoin instead of Altcoin.
from bisq.common.util.preconditions import check_argument
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.monetary.altcoin import Altcoin
from bitcoinj.base.coin import Coin

class AltcoinExchangeRate:
    """An exchange rate is expressed as a ratio of a Coin and a Altcoin amount."""
    
    _coin: Coin
    _altcoin: Altcoin

    def __init__(self, coin: Coin = None, altcoin: Altcoin = None):
        """Construct exchange rate. This amount of coin is worth that amount of altcoin."""
        if coin is None:
            coin = Coin.COIN()
        
        if altcoin is None:
            raise IllegalArgumentException("altcoin is required")

        check_argument(coin.is_positive(), "coin must be positive")
        check_argument(altcoin.is_positive(), "altcoin must be positive")
        check_argument(altcoin.currency_code is not None, "altcoin.currency_code is required")
        
        self._coin = coin
        self._altcoin = altcoin
        
    @property
    def coin(self) -> Coin:
        return self._coin
    
    @property
    def altcoin(self) -> Altcoin:
        return self._altcoin

    def coin_to_altcoin(self, convert_coin: Coin) -> Altcoin:
        """Convert a coin amount to a altcoin amount using this exchange rate."""
        converted = convert_coin.value * self._altcoin.value // self._coin.value
        
        if not (-(2**63) <= converted <= (2**63 - 1)):
            raise ArithmeticError("Overflow")
            
        return Altcoin.value_of(self._altcoin.currency_code, converted)

    def altcoin_to_coin(self, convert_altcoin: Altcoin) -> Coin:
        """Convert a altcoin amount to a coin amount using this exchange rate."""
        check_argument(convert_altcoin.currency_code == self.altcoin.currency_code, 
                       f"Currency mismatch: {convert_altcoin.currency_code} vs {self.altcoin.currency_code}")
            
        converted = convert_altcoin.value * self._coin.value // self._altcoin.value
        
        if not (-(2**63) <= converted <= (2**63 - 1)):
            raise ArithmeticError("Overflow")
            
        try:
            return Coin.value_of(converted)
        except ValueError as e:
            raise ArithmeticError(f"Overflow: {str(e)}")

    def __eq__(self, other) -> bool:
        if not isinstance(other, AltcoinExchangeRate):
            return False
        return self.coin == other.coin and self.altcoin == other.altcoin

    def __hash__(self) -> int:
        return hash((self.coin, self.altcoin))
