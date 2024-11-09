from decimal import Decimal, ROUND_HALF_UP
import locale
from typing import List, Optional, Union
from dataclasses import dataclass

import bitcoinj.base.coin
from bitcoinj.base.monetary import Monetary
import bitcoinj.base.utils.fiat as Fiat

@dataclass
class DecimalNumber:
    numbers: int
    decimals: int

class MonetaryFormat:
    """
    Utility for formatting and parsing coin values to and from human-readable form.
    
    MonetaryFormat instances are immutable. Invoking a configuration method has no effect on the receiving instance; you
    must store and use the new instance it returns, instead. Instances are thread safe, so they may be stored safely as
    static constants. 
    """
    
    # Constants
    MAX_DECIMALS = 8
    DECIMALS_PADDING = "0" * 16 #  a few more than necessary for Bitcoin
    
    # Currency codes
    CODE_BTC = "BTC"
    """Currency code for base 1 Bitcoin."""
    CODE_MBTC = "mBTC" 
    """Currency code for base 1/1000 Bitcoin."""
    CODE_UBTC = "µBTC"
    """Currency code for base 1/1000000 Bitcoin."""
    CODE_SAT = "sat"
    """Currency code for base 1 satoshi."""
    
    # Currency symbols
    SYMBOL_BTC = "₿"  # U+20BF
    """Currency symbol for base 1 Bitcoin."""
    SYMBOL_MBTC = "m₿"
    """Currency symbol for base 1/1000 Bitcoin."""
    SYMBOL_UBTC = "µ₿" 
    """Currency symbol for base 1/1000000 Bitcoin."""
    SYMBOL_SAT = "Ș"  # U+0219
    """Currency symbol for base 1 satoshi."""
    
    _btc: "MonetaryFormat" = None
    @classmethod 
    def BTC(cls):
        """Standard format for the BTC denomination."""
        if cls._btc is None:
            cls._btc = cls().with_shift(0).with_min_decimals(2).repeat_optional_decimals(2, 3)
        return cls._btc
    
    _mbtc: "MonetaryFormat" = None
    @classmethod
    def MBTC(cls):
        """Standard format for the mBTC denomination."""
        if cls._mbtc is None:
            cls._mbtc = cls().with_shift(3).with_min_decimals(2).optional_decimals(2)
        return cls._mbtc

    _ubtc: "MonetaryFormat" = None
    @classmethod
    def UBTC(cls):
        """Standard format for the µBTC denomination."""
        if cls._ubtc is None:
            cls._ubtc = cls().with_shift(6).with_min_decimals(0).optional_decimals(2)
        return cls._ubtc 
    
    _sat: "MonetaryFormat" = None  
    @classmethod
    def SAT(cls):
        """Standard format for the satoshi denomination."""
        if cls._sat is None:
            cls._sat = cls().with_shift(8).with_min_decimals(0).optional_decimals(0)
        return cls._sat
    
    _fiat: "MonetaryFormat" = None
    @classmethod
    def FIAT(cls):
        if cls._fiat is None:
            cls._fiat = cls().with_shift(0).with_min_decimals(2).repeat_optional_decimals(2, 1)
        return cls._fiat

    def __init__(self, use_symbol: bool = False,
                 negative_sign: str = '-', positive_sign: str = '',
                 zero_digit: str = '0', decimal_mark: str = '.',
                 min_decimals: int = 2, decimal_groups: Optional[List[int]] = None,
                 shift: int = 0, rounding_mode: str = ROUND_HALF_UP,
                 codes: Optional[List[str]] = "NOT_SET",
                 code_separator: str = ' ', code_prefixed: bool = True):
        self.negative_sign = negative_sign
        self.positive_sign = positive_sign  # None in Java represented as empty string
        self.zero_digit = zero_digit
        self.decimal_mark = decimal_mark
        self.min_decimals = min_decimals
        self.decimal_groups = decimal_groups
        self.shift = shift
        self.rounding_mode = rounding_mode
        
        # Initialize codes array
        if codes is "NOT_SET":
            self.codes = [None] * (self.MAX_DECIMALS + 1)
            self.codes[0] = self.SYMBOL_BTC if use_symbol else self.CODE_BTC
            self.codes[3] = self.SYMBOL_MBTC if use_symbol else self.CODE_MBTC
            self.codes[6] = self.SYMBOL_UBTC if use_symbol else self.CODE_UBTC
            self.codes[8] = self.SYMBOL_SAT if use_symbol else self.CODE_SAT
        else:
            self.codes = codes
        
        self.code_separator = code_separator
        self.code_prefixed = code_prefixed
        
    def with_negative_sign(self, negative_sign: str) -> 'MonetaryFormat':
        """
        Set character to prefix negative values.
        """
        if negative_sign.isdigit():
            raise ValueError(f"negative_sign can't be digit: {negative_sign}")
        
        if not negative_sign:
            raise ValueError("negative_sign must be non-empty")
            
        if negative_sign == self.negative_sign:
            return self
        else:
            result = MonetaryFormat(
                negative_sign=negative_sign,
                positive_sign=self.positive_sign,
                zero_digit=self.zero_digit,
                decimal_mark=self.decimal_mark,
                min_decimals=self.min_decimals,
                decimal_groups=self.decimal_groups,
                shift=self.shift,
                rounding_mode=self.rounding_mode,
                codes=self.codes,
                code_separator=self.code_separator,
                code_prefixed=self.code_prefixed,
            )
            return result
        
    def with_positive_sign(self, positive_sign: str) -> 'MonetaryFormat':
        """
        Set character to prefix positive values. A zero value means no sign is used in this case. For parsing, a missing
        sign will always be interpreted as if the positive sign was used.
        """
        if positive_sign.isdigit():
            raise ValueError(f"positive_sign can't be digit: {positive_sign}")
            
        if positive_sign == self.negative_sign:
            return self
        else:
            result = MonetaryFormat(
                negative_sign=self.negative_sign,
                positive_sign=positive_sign,
                zero_digit=self.zero_digit,
                decimal_mark=self.decimal_mark,
                min_decimals=self.min_decimals,
                decimal_groups=self.decimal_groups,
                shift=self.shift,
                rounding_mode=self.rounding_mode,
                codes=self.codes,
                code_separator=self.code_separator,
                code_prefixed=self.code_prefixed,
            )
            return result

    def digits(self, zero_digit: str) -> 'MonetaryFormat':
        """
        Set character range to use for representing digits. It starts with the specified character representing zero.
        """
        if zero_digit == self.zero_digit:
            return self
        else:
            result = MonetaryFormat(
                negative_sign=self.negative_sign,
                positive_sign=self.positive_sign,
                zero_digit=zero_digit,
                decimal_mark=self.decimal_mark,
                min_decimals=self.min_decimals,
                decimal_groups=self.decimal_groups,
                shift=self.shift,
                rounding_mode=self.rounding_mode,
                codes=self.codes,
                code_separator=self.code_separator,
                code_prefixed=self.code_prefixed,
            )
            return result

    def with_decimal_mark(self, decimal_mark: str) -> 'MonetaryFormat':
        """
        Set character to use as the decimal mark. If the formatted value does not have any decimals, no decimal mark is
        used either.
        """
        if decimal_mark.isdigit():
            raise ValueError(f"decimal_mark can't be digit: {decimal_mark}")
            
        if not decimal_mark:
            raise ValueError("decimal_mark must be non-empty")
            
        if decimal_mark == self.decimal_mark:
            return self
        else:
            result = MonetaryFormat(
                negative_sign=self.negative_sign,
                positive_sign=self.positive_sign,
                zero_digit=self.zero_digit,
                decimal_mark=decimal_mark,
                min_decimals=self.min_decimals,
                decimal_groups=self.decimal_groups,
                shift=self.shift,
                rounding_mode=self.rounding_mode,
                codes=self.codes,
                code_separator=self.code_separator,
                code_prefixed=self.code_prefixed,
            )
            return result

    def with_min_decimals(self, min_decimals: int) -> 'MonetaryFormat':
        """
        Set minimum number of decimals to use for formatting. If the value precision exceeds all decimals specified
        (including additional decimals specified by optional_decimals(int...) or repeat_optional_decimals(int, int)),
        the value will be rounded. This configuration is not relevant for parsing.
        """
        if min_decimals == self.min_decimals:
            return self
        else:
            result = MonetaryFormat(
                negative_sign=self.negative_sign,
                positive_sign=self.positive_sign,
                zero_digit=self.zero_digit,
                decimal_mark=self.decimal_mark,
                min_decimals=min_decimals,
                decimal_groups=self.decimal_groups,
                shift=self.shift,
                rounding_mode=self.rounding_mode,
                codes=self.codes,
                code_separator=self.code_separator,
                code_prefixed=self.code_prefixed,
            )
            return result

    def optional_decimals(self, groups: Union[List[int], int]) -> 'MonetaryFormat':
        """
        Set additional groups of decimals to use after the minimum decimals, if they are useful for expressing precision.
        Each value is a number of decimals in that group. If the value precision exceeds all decimals specified
        (including minimum decimals), the value will be rounded. This configuration is not relevant for parsing.
        
        For example, if you pass [4,2] it will add four decimals to your formatted string if needed, and then add
        another two decimals if needed. At this point, rather than adding further decimals the value will be rounded.
        
        param groups:
            any number numbers of decimals, one for each group
        """
        if isinstance(groups, int):
            groups = [groups]
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result
    
    def repeat_optional_decimals(self, decimals: int, repetitions: int) -> 'MonetaryFormat':
        """
        Set repeated additional groups of decimals to use after the minimum decimals, if they are useful for expressing
        precision. If the value precision exceeds all decimals specified (including minimum decimals), the value will be
        rounded. This configuration is not relevant for parsing.

        For example, if you pass decimals=1 and repetitions=8 it will add up to eight decimals to your formatted string 
        if needed. After these have been used up, rather than adding further decimals the value will be rounded.

        Args:
            decimals: value of the group to be repeated
            repetitions: number of repetitions
        """
        if repetitions < 0:
            raise ValueError(f"repetitions cannot be negative: {repetitions}")

        decimal_groups = [decimals] * repetitions

        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit, 
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result
    
    def with_shift(self, shift: int) -> 'MonetaryFormat':
        """
        Set number of digits to shift the decimal separator to the right, coming from the standard BTC notation that was
        common pre-2014. Note this will change the currency code if enabled.
        """
        if shift == self.shift:
            return self
        
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result
    
    def with_rounding_mode(self, rounding_mode: str) -> 'MonetaryFormat':
        """
        Set rounding mode to use when it becomes necessary.
        """
        if rounding_mode == self.rounding_mode:
            return self
        
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result

    def no_code(self) -> 'MonetaryFormat':
        """
        Don't display currency code when formatting. This configuration is not relevant for parsing.
        """
        if self.codes is None:
            return self
        
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=None,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result

    def code(self, code_shift: int, code: str) -> 'MonetaryFormat':
        """
        Configure currency code for given decimal separator shift. This configuration is not relevant for parsing.
        
        Args:
            code_shift: decimal separator shift, see shift()
            code: currency code
        """
        if code_shift < 0:
            raise ValueError(f"code_shift cannot be negative: {code_shift}")

        if self.codes is None:
            codes = [None] * self.MAX_DECIMALS 
        else:
            codes = self.codes.copy()
        
        codes[code_shift] = code
        
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=codes,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result
    
    def with_code_separator(self, code_separator: str) -> 'MonetaryFormat':
        """
        Separator between currency code and formatted value. This configuration is not relevant for parsing.
        """
        if code_separator.isdigit():
            raise ValueError(f"code_separator can't be digit: {code_separator}")
            
        if not code_separator:
            raise ValueError("code_separator must be positive")
            
        if code_separator == self.code_separator:
            return self
            
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=code_separator,
            code_prefixed=self.code_prefixed,
        )
        return result
    
    def prefix_code(self) -> 'MonetaryFormat':
        """
        Prefix formatted output by currency code. This configuration is not relevant for parsing.
        """
        if self.code_prefixed:
            return self
            
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=True,
        )
        return result

    def postfix_code(self) -> 'MonetaryFormat':
        """
        Postfix formatted output with currency code. This configuration is not relevant for parsing.
        """
        if not self.code_prefixed:
            return self
            
        result = MonetaryFormat(
            negative_sign=self.negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=self.zero_digit,
            decimal_mark=self.decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=False,
        )
        return result
    
    def with_locale(self, locale_str: str) -> 'MonetaryFormat':
        """
        Configure this instance with values from a Locale.
        
        Args:
            locale_str: Locale identifier string (e.g., 'en_US', 'de_DE').
        """
        original_locale = locale.getlocale(locale.LC_MONETARY)
        try:
            locale.setlocale(locale.LC_MONETARY, locale_str)
        except locale.Error as e:
            raise ValueError(f"Invalid locale: {locale_str}") from e

        conv = locale.localeconv()
        negative_sign = conv['negative_sign']
        zero_digit = '0'  # Python's locale doesn't provide zero digit directly
        decimal_mark = conv['mon_decimal_point']
        locale.setlocale(locale.LC_MONETARY, original_locale)
        
        return MonetaryFormat(
            negative_sign=negative_sign,
            positive_sign=self.positive_sign,
            zero_digit=zero_digit,
            decimal_mark=decimal_mark,
            min_decimals=self.min_decimals,
            decimal_groups=self.decimal_groups,
            shift=self.shift,
            rounding_mode=self.rounding_mode,
            codes=self.codes,
            code_separator=self.code_separator,
            code_prefixed=self.code_prefixed,
        )

    def format(self, monetary: Monetary) -> str:
        # determine maximum number of decimals that can be visible in the formatted string
        # (if all decimal groups were to be used)
        max = self.min_decimals
        if self.decimal_groups:
            max += sum(self.decimal_groups)
        max_visible_decimals = max

        smallest_unit_exponent = monetary.smallest_unit_exponent()
        if max_visible_decimals > smallest_unit_exponent:
            raise ValueError(f"max_visible_decimals cannot exceed {smallest_unit_exponent}")

        # Convert to decimal
        satoshis = abs(monetary.get_value())
        decimal_shift = smallest_unit_exponent - self.shift
        decimal = self._satoshis_to_decimal(satoshis, self.rounding_mode, decimal_shift, max_visible_decimals)
        numbers = decimal.numbers
        decimals = decimal.decimals

        # Formatting
        str = f"{decimals:0{decimal_shift}d}" if decimal_shift > 0 else ""
        while len(str) > self.min_decimals and str[-1] == '0':
            str = str[:-1]
        i = self.min_decimals
        if self.decimal_groups is not None:
            for group in self.decimal_groups:
                if i < len(str) < i + group:
                    str = str.ljust(i + group, '0')
                    break
                i += group
        if str:
            str = self.decimal_mark + str
        formatted = f"{numbers}{str}"
        if monetary.get_value() < 0:
            formatted = self.negative_sign + formatted
        elif self.positive_sign:
            formatted = self.positive_sign + formatted
        if self.codes is not None:
            if self.code_prefixed:
                formatted = f"{self.currency_code()}{self.code_separator}{formatted}"
            else:
                formatted = f"{formatted}{self.code_separator}{self.currency_code()}"

        # Convert to non-Arabic digits
        if self.zero_digit != '0':
            offset = ord(self.zero_digit) - ord('0')
            formatted = ''.join(
                chr(ord(c) + offset) if c.isdigit() else c for c in formatted
            )

        return formatted

    def _satoshis_to_decimal(self, satoshis: int, rounding_mode: str, decimal_shift: int, max_visible_decimals: int) -> DecimalNumber:
        """
        Convert a long number of satoshis to a decimal number of BTC

        Args:
            satoshis: number of satoshis
            rounding_mode: rounding mode
            decimal_shift: the number of places to move the decimal point to the left, coming from smallest unit (e.g. satoshi)
            max_decimals: the maximum number of decimals that can be visible in the formatted string
        
        Returns:
            DecimalNumber instance with whole and fraction parts.
        """
        decimal_sats = Decimal(satoshis)
        # shift the decimal point
        decimal_sats = decimal_sats.scaleb(-decimal_shift)
        # discard unwanted precision and round accordingly
        decimal_sats = decimal_sats.quantize(
            Decimal('1.' + '0' * max_visible_decimals),
            rounding=rounding_mode
        )
        # separate decimals from the number
        integer_part, fractional_part = divmod(decimal_sats, 1)
        fraction = int(
            (fractional_part * Decimal(10 ** decimal_shift)).to_integral_value()
        )
        return DecimalNumber(int(integer_part), fraction)
    
    def parse(self, string: str) -> Monetary:
        return bitcoinj.base.coin.Coin.value_of(self._parse_value(string, bitcoinj.base.coin.Coin.SMALLEST_UNIT_EXPONENT))
    
    def parse_fiat(self, currency_code: str, string: str):
        """
        Parse a human-readable fiat value to a Fiat instance.
        
        Raises:
            ValueError: if the string cannot be parsed
        """
        value = self._parse_value(string, Fiat.Fiat.SMALLEST_UNIT_EXPONENT)
        return Fiat.Fiat(currency_code, value)

    def _parse_value(self, string: str, smallest_unit_exponent: int) -> int:
        if len(self.DECIMALS_PADDING) < smallest_unit_exponent:
            raise ValueError(
                f"smallest_unit_exponent can't be higher than {len(self.DECIMALS_PADDING)}: {smallest_unit_exponent}"
            )
            
        if not string:
            raise ValueError("empty string")
            
        # Handle sign
        first = string[0]
        if first in (self.negative_sign, self.positive_sign):
            string = string[1:]
        
        # Split into numbers and decimals
        parts = string.split(self.decimal_mark)
        if len(parts) > 2:
            raise ValueError("more than one decimal mark")
        elif len(parts) == 2:
            numbers, decimals = parts
            # Pad decimals with zeros
            decimals = (decimals + self.DECIMALS_PADDING)
        else:
            numbers = parts[0]
            decimals = self.DECIMALS_PADDING
        
        # Construct full value string with proper decimal shift
        value_str = numbers + decimals[:smallest_unit_exponent - self.shift]
        
        # Validate all characters are digits
        if not all(c.isdigit() for c in value_str):
            invalid_char = next(c for c in value_str if not c.isdigit())
            raise ValueError(f"illegal character: {invalid_char}")
        
        # Parse to integer
        value = int(value_str)
        
        # Apply sign
        if first == self.negative_sign:
            value = -value
            
        return value

    def currency_code(self) -> Optional[str]:
        """Get currency code that will be used for current shift."""
        if self.codes is None:
            return None
        if self.codes[self.shift] is None:
            raise ValueError(f"Missing code for shift: {self.shift}")
        return self.codes[self.shift]
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MonetaryFormat):
            return False
        return self.__dict__ == value.__dict__
        
    def __hash__(self) -> int:
        return hash((self.negative_sign, self.positive_sign, self.zero_digit, self.decimal_mark, self.min_decimals, self.decimal_groups, self.shift, self.rounding_mode, tuple(self.codes), self.code_separator, self.code_prefixed))
    
    
FIAT_FRIENDLY_FORMAT = MonetaryFormat.FIAT().postfix_code()    
FIAT_PLAIN_FORMAT = (
         MonetaryFormat.FIAT()
        .with_min_decimals(0)
        .repeat_optional_decimals(1, 4)
        .no_code()
    )

COIN_FRIENDLY_FORMAT = MonetaryFormat.BTC().with_min_decimals(2).repeat_optional_decimals(1, 6).postfix_code()
COIN_PLAIN_FORMAT = MonetaryFormat.BTC().with_min_decimals(0).repeat_optional_decimals(1, 8).no_code()