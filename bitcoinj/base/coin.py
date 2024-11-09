
from decimal import Decimal, InvalidOperation
from typing import Union
from bitcoinj.base.monetary import Monetary
import bitcoinj.base.utils.monetary_format


class Coin(Monetary):
    
    SMALLEST_UNIT_EXPONENT = 8
    """Number of decimals for one Bitcoin. This constant is useful for quick adapting to other coins because a lot of constants derive from it."""
    
    COIN_VALUE = 100_000_000
    """The number of satoshis equal to one bitcoin."""
    
    _zero: "Coin" = None
    @classmethod
    def ZERO(cls):
        """
        Zero Bitcoins.
        """
        if cls._zero is None:
            cls._zero = cls(0)
        return cls._zero
    
    _coin: "Coin" = None
    @classmethod
    def COIN(cls):
        """
        One Bitcoin.
        """
        if cls._coin is None:
            cls._coin = cls(cls.COIN_VALUE)
        return cls._coin
    
    _cent: "Coin" = None
    @classmethod
    def CENT(cls):
        """
        0.01 Bitcoins. This unit is not really used much.
        """
        if cls._cent is None:
            cls._cent = cls.COIN().divide(100)
        return cls._cent
    
    _millicoin: "Coin" = None
    @classmethod
    def MILLICOIN(cls):
        """
         0.001 Bitcoins, also known as 1 mBTC.
        """
        if cls._millicoin is None:
            cls._millicoin = cls.COIN().divide(1_000)
        return cls._millicoin
    
    _microcoin: "Coin" = None
    @classmethod
    def MICROCOIN(cls):
        """
        0.000001 Bitcoins, also known as 1 µBTC or 1 uBTC.
        """
        if cls._microcoin is None:
            cls._microcoin = cls.MILLICOIN().divide(1_000)
        return cls._microcoin
    
    _satoshi: "Coin" = None
    @classmethod
    def SATOSHI(cls):
        """
        A satoshi is the smallest unit that can be transferred. 100 million of them fit into a Bitcoin.
        """
        if cls._satoshi is None:
            cls._satoshi = cls(1)
        return cls._satoshi
    
    _fifty_coins: "Coin" = None
    @classmethod
    def FIFTY_COINS(cls):
        if cls._fifty_coins is None:
            cls._fifty_coins = cls.COIN().multiply(50)
        return cls._fifty_coins
    
    _negative_satoshi: "Coin" = None
    @classmethod
    def NEGATIVE_SATOSHI(cls):
        if cls._negative_satoshi is None:
            cls._negative_satoshi = cls(-1)
        return cls._negative_satoshi
    
    def __init__(self, satoshis: int) -> None:
        super().__init__()
        self.value = satoshis
        """The number of satoshis of this monetary value."""
    
    @staticmethod
    def value_of(satoshis_or_coins: int, cents: int = None) -> 'Coin':
        """
        if second argument is passed, first argument is coins and second argument is cents
        if second argument is not passed, first argument is satoshis
        """
        if cents is not None:
            # first arg is coins
            """
            checkArgument(cents < 100, () -> "cents nust be below 100: " + cents);
            checkArgument(cents >= 0, () -> "cents cannot be negative: " + cents);
            checkArgument(coins >= 0, () -> "coins cannot be negative: " + cents);
            """
            if cents >= 100:
                raise ValueError(f"cents must be below 100: {cents}")
            if cents < 0: 
                raise ValueError(f"cents cannot be negative: {cents}")
            if satoshis_or_coins < 0:
                raise ValueError(f"coins cannot be negative: {cents}")
            return Coin.COIN().multiply(satoshis_or_coins).add(Coin.CENT().multiply(cents))
        # first arg is satoshis
        # Avoid allocating a new object for Coins of value zero
        if satoshis_or_coins == 0:
            return Coin.ZERO()
        return Coin(satoshis_or_coins)
        
    def smallest_unit_exponent(self) -> int:
        return self.SMALLEST_UNIT_EXPONENT
        
    def get_value(self) -> int:
        return self.value
    
    @staticmethod
    def btc_to_satoshi(coins: Decimal) -> int:
        try:
            result = int(coins * Decimal(10 ** Coin.SMALLEST_UNIT_EXPONENT))
            if not isinstance(result, int):
                raise ValueError("Conversion would result in fractional satoshis")
            return result
        except InvalidOperation as e:
            raise ValueError(f"Invalid BTC amount: {e}")
        except OverflowError as e:
            raise OverflowError(f"BTC amount too large to convert: {e}")

    @staticmethod
    def satoshi_to_btc(satoshis: int) -> Decimal:
        return Decimal(satoshis) / Decimal(10 ** Coin.SMALLEST_UNIT_EXPONENT)
    
    @staticmethod
    def of_btc(coins: Decimal):
        return Coin.value_of(Coin.btc_to_satoshi(coins))
    
    @staticmethod
    def of_sat(satoshis: int):
        return Coin.value_of(satoshis)
    
    @staticmethod
    def parse_coin(string: str):
        try:
            btc_amount = Decimal(string)
            satoshis = Coin.btc_to_satoshi(btc_amount)
            return Coin.value_of(satoshis)
        except (InvalidOperation, ValueError, OverflowError) as e:
            raise ValueError(f"Invalid coin amount: {str(e)}")
        
    @staticmethod
    def parse_coin_inexact(string: str):
        try:
            # Convert string to Decimal and shift decimal point right
            satoshis = int(Decimal(string) * Decimal(10 ** Coin.SMALLEST_UNIT_EXPONENT))
            return Coin.value_of(satoshis)
        except ArithmeticError as e:
            raise ValueError(str(e))
        
    def add(self, value: 'Coin') -> 'Coin':
        return Coin.value_of(self.value + value.value)

    # Python special method for addition
    __add__ = add

    def subtract(self, other: 'Coin') -> 'Coin':
        return Coin.value_of(self.value - other.value)

    # Python special method for subtraction
    __sub__ = subtract

    def multiply(self, factor: int) -> 'Coin':
        return Coin.value_of(self.value * factor)

    # Python special methods for multiplication
    __mul__ = multiply
    __rmul__ = multiply

    def divide(self, divisor: Union[int, 'Coin']):
        if isinstance(divisor, Coin):
            return self.value // divisor.value
        return Coin.value_of(self.value // divisor)

    # Python special method for division
    __truediv__ = divide
    __floordiv__ = divide

    def divide_and_remainder(self, divisor: int):
        quotient = self.value // divisor
        remainder = self.value % divisor
        return (Coin.value_of(quotient), Coin.value_of(remainder))
    
    def is_positive(self) -> bool:
        """Returns True if this instance represents a monetary value greater than zero."""
        return self.signum() == 1

    def is_negative(self) -> bool:
        """Returns True if this instance represents a monetary value less than zero."""
        return self.signum() == -1

    def is_zero(self) -> bool:
        """Returns True if this instance represents zero monetary value."""
        return self.signum() == 0

    def is_greater_than(self, other: 'Coin') -> bool:
        """Returns True if this value is greater than the other Coin."""
        return self.__gt__(other)

    def is_less_than(self, other: 'Coin') -> bool:
        """Returns True if this value is less than the other Coin."""
        return self.__lt__(other)

    def shift_left(self, n: int) -> 'Coin':
        """Shifts the value left by n bits."""
        return Coin.value_of(self.value << n)

    def shift_right(self, n: int) -> 'Coin':
        """Shifts the value right by n bits."""
        return Coin.value_of(self.value >> n)

    def signum(self) -> int:
        """Returns the sign of the value (-1, 0, or 1)."""
        if self.value == 0:
            return 0
        return -1 if self.value < 0 else 1

    def negate(self) -> 'Coin':
        """Returns the negation of this value."""
        return Coin.value_of(-self.value)
    
    def to_friendly_string(self) -> str:
        return bitcoinj.base.utils.monetary_format.COIN_FRIENDLY_FORMAT.format(self)
    
    def to_plain_string(self) -> str:
        return bitcoinj.base.utils.monetary_format.COIN_PLAIN_FORMAT.format(self)

    # Rich comparison methods
    def __lt__(self, other: 'Coin') -> bool:
        return self.value < other.value

    def __gt__(self, other: 'Coin') -> bool:
        return self.value > other.value
    
    def to_sat(self):
        return self.value
    
    def to_btc(self):
        return self.satoshi_to_btc(self.value)
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Coin) and self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
    