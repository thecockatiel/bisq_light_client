from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat

class ExchangeRate:
    """An exchange rate is expressed as a ratio of a Coin and a Fiat amount."""
    _coin: Coin
    _fiat: Fiat

    def __init__(self, coin: Coin = None, fiat: Fiat = None):
        """Construct exchange rate. This amount of coin is worth that amount of fiat."""
        if coin is None:
            coin = Coin.COIN()
        
        if fiat is None:
            raise ValueError("fiat is required")

        assert coin.is_positive(), "coin must be positive"
        assert fiat.is_positive(), "fiat must be positive"
        assert fiat.currency_code is not None, "fiat.currency_code is required"
        
        self._coin = coin
        self._fiat = fiat
        
    @property
    def coin(self) -> Coin:
        return self._coin
    
    @property
    def fiat(self) -> Fiat:
        return self._fiat

    def coin_to_fiat(self, convert_coin: Coin) -> Fiat:
        """Convert a coin amount to a fiat amount using this exchange rate."""
        converted = convert_coin.value * self._fiat.value // self._coin.value
        
        if not (-(2**63) <= converted <= (2**63 - 1)):
            raise ArithmeticError("Overflow")
            
        return Fiat.value_of(self._fiat.currency_code, converted)

    def fiat_to_coin(self, convert_fiat: Fiat) -> Coin:
        """Convert a fiat amount to a coin amount using this exchange rate."""
        assert convert_fiat.currency_code == self.fiat.currency_code, \
            f"Currency mismatch: {convert_fiat.currency_code} vs {self.fiat.currency_code}"
            
        converted = convert_fiat.value * self._coin.value // self._fiat.value
        
        if not (-(2**63) <= converted <= (2**63 - 1)):
            raise ArithmeticError("Overflow")
            
        try:
            return Coin.value_of(converted)
        except ValueError as e:
            raise ArithmeticError(f"Overflow: {str(e)}")

    def __eq__(self, other) -> bool:
        if not isinstance(other, ExchangeRate):
            return False
        return self.coin == other.coin and self.fiat == other.fiat

    def __hash__(self) -> int:
        return hash((self.coin, self.fiat))
