from typing import TYPE_CHECKING, Union
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.res import Res
from utils.java.decimal_format import DecimalFormat
from bisq.core.locale.currency_util import is_fiat_currency
from bitcoinj.base.utils.monetary_format import MonetaryFormat
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from utils.formatting import readable_file_size

if TYPE_CHECKING:
    from bisq.core.monetary.altcoin import Altcoin
    from bisq.core.monetary.price import Price
    
logger = get_logger(__name__)

class FormattingUtils:
    BTC_FORMATTER_KEY = "BTC"
    
    RANGE_SEPARATOR = " - "
    
    fiat_price_format = MonetaryFormat().with_shift(0).with_min_decimals(4).repeat_optional_decimals(0, 0)
    altcoin_format = MonetaryFormat().with_shift(0).with_min_decimals(8).repeat_optional_decimals(0, 0)
    decimal_format = DecimalFormat("#.#")
    
    @staticmethod
    def format_coin_with_code(value: Union[int,"Coin"], coin_format: "MonetaryFormat"):
        if isinstance(value, int):
            value = Coin.value_of(value)
        if value is not None:
            try:
                # we don't use the code feature from coin_format as it does automatic switching between mBTC and BTC and
                # pre and post fixing
                return coin_format.postfix_code().format(value)
            except Exception as e:
                logger.warning(f"Exception at format_coin_with_code: {e}")
                return ""
        else:
            return ""

    @staticmethod
    def format_coin(value: Union[int, "Coin"], coin_format: "MonetaryFormat", decimal_places: int = -1, decimal_aligned: bool = False, max_number_of_digits: int = 0):
        if isinstance(value, int):
            value = Coin.value_of(value)
        formatted_coin = ""

        if value is not None:
            try:
                if decimal_places < 0 or decimal_places > 4:
                    formatted_coin = coin_format.no_code().format(value)
                else:
                    formatted_coin = coin_format.no_code().with_min_decimals(decimal_places).repeat_optional_decimals(1, decimal_places).format(value)
            except Exception as e:
                logger.warning(f"Exception at format_coin: {e}")

        if decimal_aligned:
            formatted_coin = FormattingUtils.fill_up_places_with_empty_strings(formatted_coin, max_number_of_digits)

        return formatted_coin

    @staticmethod
    def fill_up_places_with_empty_strings(formatted_number: str, max_number_of_digits: int) -> str:
        # FIXME(java): temporary deactivate adding spaces in front of numbers as we don't use a monospace font right now.
        # formatted_number = formatted_number.rjust(max_number_of_digits)
        return formatted_number

    @staticmethod
    def format_fiat(fiat: "Fiat", format: "MonetaryFormat", append_currency_code: bool) -> str:
        if fiat is not None:
            try:
                res = format.no_code().format(fiat)
                if append_currency_code:
                    return res + " " + fiat.currency_code
                else:
                    return res
            except Exception as e:
                logger.warning(f"Exception at format_fiat: {e}")
                return Res.get("shared.na") + " " + fiat.currency_code
        else:
            return Res.get("shared.na")

    @staticmethod
    def format_altcoin(altcoin: "Altcoin", append_currency_code: bool) -> str:
        if altcoin is not None:
            try:
                res = FormattingUtils.altcoin_format.no_code().format(altcoin)
                if append_currency_code:
                    return res + " " + altcoin.currency_code
                else:
                    return res
            except Exception as e:
                logger.warning(f"Exception at format_altcoin: {e}")
                return Res.get("shared.na") + " " + altcoin.currency_code
        else:
            return Res.get("shared.na")

    @staticmethod
    def format_altcoin_volume(altcoin: "Altcoin", append_currency_code: bool) -> str:
        if altcoin is not None:
            try:
                # TODO quick hack... (java?)
                if altcoin.currency_code == "BSQ":
                    res = FormattingUtils.altcoin_format.no_code().with_min_decimals(2).repeat_optional_decimals(0, 0).format(altcoin)
                else:
                    res = FormattingUtils.altcoin_format.no_code().format(altcoin)
                if append_currency_code:
                    return res + " " + altcoin.currency_code
                else:
                    return res
            except Exception as e:
                logger.warning(f"Exception at format_altcoin_volume: {e}")
                return Res.get("shared.na") + " " + altcoin.currency_code
        else:
            return Res.get("shared.na")

    @staticmethod
    def format_price(price: "Price", price_format: "MonetaryFormat" = None, append_currency_code: bool = False) -> str:
        if price_format is None:
            price_format = FormattingUtils.fiat_price_format
            
        if price is not None:
            monetary = price.monetary
            if isinstance(monetary, Fiat):
                return FormattingUtils.format_fiat(monetary, price_format, append_currency_code)
            else:
                return FormattingUtils.format_altcoin(monetary, append_currency_code)
        else:
            return Res.get("shared.na")

    @staticmethod
    def format_market_price(price: float, currency_code: str = None, precision: int = None) -> str:
        if precision is None:
            if is_fiat_currency(currency_code):
                return FormattingUtils.format_market_price(price, 2)
            else:
                return FormattingUtils.format_market_price(price, 8)
        return FormattingUtils.format_rounded_double_with_precision(price, precision)

    @staticmethod
    def format_rounded_double_with_precision(value: float, precision: int) -> str:
        FormattingUtils.decimal_format.set_minimum_fraction_digits(precision)
        FormattingUtils.decimal_format.set_maximum_fraction_digits(precision)
        return FormattingUtils.decimal_format.format(
            MathUtils.round_double(value, precision)
        ).replace(",", ".")

    @staticmethod
    def format_to_percent_with_symbol(value: float) -> str:
        return FormattingUtils.format_to_percent(value) + "%"

    @staticmethod
    def format_to_rounded_percent_with_symbol(value: float) -> str:
        rounded_format = DecimalFormat("#")
        return FormattingUtils.format_to_percent(value, rounded_format) + "%"

    @staticmethod
    def format_percentage_price(value: float) -> str:
        return FormattingUtils.format_to_percent_with_symbol(value)

    @staticmethod
    def format_to_percent(value: float, decimal_format: DecimalFormat = None) -> str:
        if decimal_format is None:
            decimal_format = DecimalFormat("#.##")
            decimal_format.set_minimum_fraction_digits(2)
            decimal_format.set_maximum_fraction_digits(2)
        
        return decimal_format.format(
            MathUtils.round_double(value * 100.0, 2)
        ).replace(",", ".")

    @staticmethod
    def format_bytes(amount: int):
        return readable_file_size(amount)
    
    # TODO: implement rest
