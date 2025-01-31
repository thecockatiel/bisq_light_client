from decimal import Decimal
from functools import total_ordering
from utils.preconditions import check_argument
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bitcoinj.base.monetary import Monetary
from bitcoinj.base.utils.monetary_format import (
    ALTCOIN_FRIENDLY_FORMAT,
    ALTCOIN_PLAIN_FORMAT,
)

@total_ordering
class Altcoin(Monetary):
    SMALLEST_UNIT_EXPONENT = 8
    FRIENDLY_FORMAT = ALTCOIN_FRIENDLY_FORMAT
    PLAIN_FORMAT = ALTCOIN_PLAIN_FORMAT

    def __init__(self, currency_code: str, value: int):
        self._value = value
        """
        The number of smallest units of this monetary value.
        """
        self._currency_code = currency_code

    @property
    def value(self) -> int:
        return self._value

    @property
    def currency_code(self) -> str:
        return self._currency_code
    
    @staticmethod
    def value_of(currency_code: str, value: int):
        return Altcoin(currency_code, value)

    def smallest_unit_exponent(self) -> int:
        return Altcoin.SMALLEST_UNIT_EXPONENT

    def get_value(self) -> int:
        return self._value

    @classmethod
    def parse_altcoin(cls, currency_code:str, input: str):
        from bisq.core.util.parsing_utils import ParsingUtils
        try:
            cleaned = ParsingUtils.convert_chars_for_number(input)
            # First multiply to shift decimal places
            scaled = Decimal(cleaned) * Decimal(10**cls.SMALLEST_UNIT_EXPONENT)
            # Check if value would fit in an integer
            check_argument(scaled.is_finite() and scaled == scaled.to_integral_exact(), 
                         "Cannot convert to exact integer value")
            val = int(scaled)
            return cls(currency_code, val)
        except Exception as e:
            raise IllegalArgumentException(e)
    
    def add(self, other: "Altcoin") -> "Altcoin":
        check_argument(other.currency_code == self.currency_code,
                      f"Cannot add different currencies: {other.currency_code} vs {self.currency_code}")
        return Altcoin(self.currency_code, self.value + other.value)

    def subtract(self, other: "Altcoin") -> "Altcoin":
        check_argument(other.currency_code == self.currency_code,
                      f"Cannot subtract different currencies: {other.currency_code} vs {self.currency_code}")
        return Altcoin(self.currency_code, self.value - other.value)

    def multiply(self, factor: int) -> "Altcoin":
        return Altcoin(self.currency_code, self.value * factor)

    def divide(self, divisor) -> "Altcoin":
        if isinstance(divisor, Altcoin):
            check_argument(divisor.currency_code == self.currency_code,
                         f"Cannot divide different currencies: {divisor.currency_code} vs {self.currency_code}")
            return self.value // divisor.value
        return Altcoin(self.currency_code, self.value // divisor)

    def divide_and_remainder(self, divisor: int) -> tuple["Altcoin", "Altcoin"]:
        quotient = self.value // divisor
        remainder = self.value % divisor
        return (Altcoin(self.currency_code, quotient), Altcoin(self.currency_code, remainder))

    def is_positive(self) -> bool:
        """
        Returns true if and only if this instance represents a monetary value greater than zero, otherwise false.
        """
        return self.signum() == 1

    def is_negative(self) -> bool:
        """
        Returns true if and only if this instance represents a monetary value less than zero, otherwise false.
        """
        return self.signum() == -1

    def is_zero(self) -> bool:
        """
        Returns true if and only if this instance represents zero monetary value, otherwise false.
        """
        return self.signum() == 0

    def signum(self) -> int:
        if self.value == 0:
            return 0
        return -1 if self.value < 0 else 1

    def negate(self) -> "Altcoin":
        return Altcoin(self.currency_code, -self.value)
    
    def to_friendly_string(self) -> str:
        return Altcoin.FRIENDLY_FORMAT.code(0, self._currency_code).format(self)

    def to_plain_string(self) -> str:
        return Altcoin.PLAIN_FORMAT.format(self)

    def __str__(self) -> str:
        return self.to_plain_string()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Altcoin):
            return NotImplemented
        return self.value == other.value and self.currency_code == other.currency_code

    def __lt__(self, other: "Altcoin") -> bool:
        if not isinstance(other, Altcoin):
            return NotImplemented
        if self.currency_code != other.currency_code:
            return self.currency_code < other.currency_code
        return self.value < other.value
    
    def __hash__(self) -> int:
        return hash((self.value, self.currency_code))
