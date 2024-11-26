from typing import Union

from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.util.formatting_util import FormattingUtils
from bitcoinj.base.coin import Coin
from bisq.core.util.coin.coin_formatter import CoinFormatter
from bitcoinj.base.utils.monetary_format import MonetaryFormat


logger = get_logger(__name__)

# NOTE: I guess performance can be increased a little for clean_double_input usages

class ParsingUtils:    
    @staticmethod
    def parse_to_coin(input_str: str, formatter: Union['CoinFormatter', 'MonetaryFormat']) -> 'Coin':
        if isinstance(formatter, CoinFormatter):
            formatter = formatter.get_monetary_format()

        if input_str is not None and len(input_str) > 0:
            try:
                return formatter.parse(ParsingUtils.clean_double_input(input_str))
            except Exception as e:
                logger.warning(f"Exception at parse_to_coin: {str(e)}")

        return Coin.ZERO()
    
    @staticmethod
    def parse_number_string_to_double(input_str: str) -> float:
        return float(ParsingUtils.clean_double_input(input_str))

    @staticmethod
    def parse_percent_string_to_double(percent_string: str) -> float:
        input_str = percent_string.replace("%", "")
        input_str = ParsingUtils.clean_double_input(input_str)
        value = float(input_str)
        return MathUtils.round_double(value / 100, 4)

    @staticmethod
    def parse_price_string_to_long(currency_code: str, amount: str, precision: int) -> int:
        from bisq.core.monetary.price import Price
        if not amount:
            return 0

        try:
            amount_value = float(amount)
            amount = FormattingUtils.format_rounded_double_with_precision(amount_value, precision)
            return Price.parse(currency_code, amount).value
        except ValueError:
            # expected ValueError if input is not a number
            pass
        except Exception as e:
            logger.error(f"parse_price_string_to_long: {str(e)}")
        return 0

    @staticmethod
    def convert_chars_for_number(input_str: str) -> str:
        # Some languages like Finnish use the long dash for the minus
        input_str = input_str.replace('−', '-')
        # Remove all whitespace
        input_str = input_str.translate(str.maketrans('', '', ' \t\n\r'))
        # Replace comma with decimal point
        return input_str.replace(',', '.')

    @staticmethod
    def clean_double_input(input_str: str) -> str:
        input_str = ParsingUtils.convert_chars_for_number(input_str)
        if input_str == ".":
            input_str = "0."
        if input_str == "-.":
            input_str = "-0."
        # Validate that the string can be parsed as a float
        # This will throw ValueError if invalid
        float(input_str)
        return input_str
