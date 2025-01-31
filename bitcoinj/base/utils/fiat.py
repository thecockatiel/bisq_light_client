from decimal import ROUND_DOWN, Decimal
from functools import total_ordering
from typing import Tuple

from bisq.common.util.preconditions import check_argument
from bitcoinj.base.monetary import Monetary
import bitcoinj.base.utils.monetary_format

@total_ordering
class Fiat(Monetary):
    """
    Represents a monetary fiat value. It was decided to not fold this into {@link Coin} because of type
    safety. Fiat values always come with an attached currency code.

    This class is immutable.
    """

    SMALLEST_UNIT_EXPONENT = 4
    """
    The absolute value of exponent of the value of a "smallest unit" in scientific notation. 
    We picked 4 rather than 2, because in financial applications it's common to use sub-cent precision.
    """

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
        return Fiat(currency_code, value)

    def smallest_unit_exponent(self) -> int:
        return Fiat.SMALLEST_UNIT_EXPONENT

    def get_value(self) -> int:
        return self._value

    @classmethod
    def parse_fiat(cls, currency_code: str, value_str: str) -> "Fiat":
        """
        Parses an amount expressed in the way humans are used to
        This takes string in a format supporting scientific notion, for example "0", "1", "0.10", "1.23E3", "1234.5E-5".

        raises ValueError if you try to specify more than 4 digits after the comma, or a value out of range.
        """
        try:
            # First multiply to shift decimal places
            scaled = Decimal(value_str) * Decimal(10**cls.SMALLEST_UNIT_EXPONENT)
            # Check if value would fit in an integer
            check_argument(scaled.is_finite() and scaled == scaled.to_integral_exact(), 
                         "Cannot convert to exact integer value")
            val = int(scaled)
            return cls(currency_code, val)
        except ArithmeticError as e:
            raise ValueError(str(e))

    @classmethod
    def parse_fiat_inexact(cls, currency_code: str, value_str: str) -> "Fiat":
        """
        Parses an amount expressed in the way humans are used to
        This takes string in a format supporting scientific notion, for example "0", "1", "0.10", "1.23E3", "1234.5E-5".

        raises ValueError if you try to specify a value out of range.
        """
        try:
            val = int(Decimal(value_str) * Decimal(10**cls.SMALLEST_UNIT_EXPONENT))
            return cls(currency_code, val)
        except ArithmeticError as e:
            raise ValueError(str(e))

    def add(self, other: "Fiat") -> "Fiat":
        check_argument(other.currency_code == self.currency_code,
                      f"Cannot add different currencies: {other.currency_code} vs {self.currency_code}")
        return Fiat(self.currency_code, self.value + other.value)

    def subtract(self, other: "Fiat") -> "Fiat":
        check_argument(other.currency_code == self.currency_code,
                      f"Cannot subtract different currencies: {other.currency_code} vs {self.currency_code}")
        return Fiat(self.currency_code, self.value - other.value)

    def multiply(self, factor: int) -> "Fiat":
        return Fiat(self.currency_code, self.value * factor)

    def divide(self, divisor) -> "Fiat":
        if isinstance(divisor, Fiat):
            check_argument(divisor.currency_code == self.currency_code,
                         f"Cannot divide different currencies: {divisor.currency_code} vs {self.currency_code}")
            return self.value // divisor.value
        return Fiat(self.currency_code, self.value // divisor)

    def divide_and_remainder(self, divisor: int) -> Tuple["Fiat", "Fiat"]:
        quotient = self.value // divisor
        remainder = self.value % divisor
        return (Fiat(self.currency_code, quotient), Fiat(self.currency_code, remainder))

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

    def negate(self) -> "Fiat":
        return Fiat(self.currency_code, -self.value)

    def to_friendly_string(self) -> str:
        """
        Returns the value as a 0.12 type string. More digits after the decimal place will be used if necessary, but two
        will always be present.
        """
        return bitcoinj.base.utils.monetary_format.FIAT_FRIENDLY_FORMAT.code(0, self._currency_code).format(self)

    def to_plain_string(self) -> str:
        """
        Returns the value as a plain string. The result is unformatted with no trailing zeroes. For
        instance, a value of 150000 "smallest units" gives an output string of "0.0015".
        """
        return bitcoinj.base.utils.monetary_format.FIAT_PLAIN_FORMAT.format(self)

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fiat):
            return NotImplemented
        return self.value == other.value and self.currency_code == other.currency_code

    def __lt__(self, other: "Fiat") -> bool:
        if not isinstance(other, Fiat):
            return NotImplemented
        if self.currency_code != other.currency_code:
            return self.currency_code < other.currency_code
        return self.value < other.value
    
    def __hash__(self) -> int:
        return hash((self.value, self.currency_code))
