from typing import TYPE_CHECKING, Optional
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.util.formatting_util import FormattingUtils
from bisq.core.util.parsing_utils import ParsingUtils
from bitcoinj.base.utils.fiat import Fiat

if TYPE_CHECKING:
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.user.preferences import Preferences


# TODO
class PriceUtil:

    def __init__(
        self,
        price_feed_service: "PriceFeedService",
        trade_statistics_manager: "TradeStatisticsManager",
        preferences: "Preferences",
    ):
        self.price_feed_service = price_feed_service
        self.trade_statistics_manager = trade_statistics_manager
        self.preferences = preferences
        self.bsq_30_day_average_price: Optional[Price] = None

    @staticmethod
    def get_market_price_as_long(input_value: str, currency_code: str) -> int:
        if not input_value or not currency_code:
            return 0

        try:
            precision = PriceUtil.get_market_price_precision(currency_code)
            string_value = PriceUtil.reformat_market_price(input_value, currency_code)
            return ParsingUtils.parse_price_string_to_long(
                currency_code, string_value, precision
            )
        except Exception:
            return 0

    @staticmethod
    def reformat_market_price(input_value: str, currency_code: str) -> str:
        if not input_value or not currency_code:
            return ""

        price_as_double = ParsingUtils.parse_number_string_to_double(input_value)
        precision = PriceUtil.get_market_price_precision(currency_code)
        return FormattingUtils.format_rounded_double_with_precision(
            price_as_double, precision
        )

    @staticmethod
    def format_market_price(price: int, currency_code: str) -> str:
        market_price_precision = PriceUtil.get_market_price_precision(currency_code)
        scaled = MathUtils.scale_down_by_power_of_10(price, market_price_precision)
        return FormattingUtils.format_market_price(scaled, market_price_precision)

    @staticmethod
    def get_market_price_precision(currency_code: str) -> int:
        return (
            Altcoin.SMALLEST_UNIT_EXPONENT
            if is_crypto_currency(currency_code)
            else Fiat.SMALLEST_UNIT_EXPONENT
        )
