from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.btc.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.currency_util import is_crypto_currency, is_fiat_currency
from bisq.core.util.average_price_util import get_average_price_tuple

if TYPE_CHECKING:
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.user.preferences import Preferences

logger = get_logger(__name__)


class CorePriceService:
    def __init__(
        self,
        preferences: "Preferences",
        price_feed_service: "PriceFeedService",
        trade_statistics_manager: "TradeStatisticsManager",
    ):
        self.preferences = preferences
        self.price_feed_service = price_feed_service
        self.trade_statistics_manager = trade_statistics_manager

    def _is_currency_code(self, currency_code: str) -> bool:
        return is_fiat_currency(currency_code) or is_crypto_currency(currency_code)

    def get_market_price(
        self, currency_code: str, result_handler: Callable[[float], None]
    ) -> float:
        upper_case_currency_code = currency_code.upper()

        if not self._is_currency_code(upper_case_currency_code):
            raise IllegalStateException(
                f"{upper_case_currency_code} is not a valid currency code"
            )

        if not self.price_feed_service.has_prices:
            raise IllegalStateException("price feed service has no prices")

        try:
            self.price_feed_service.currency_code = upper_case_currency_code
        except Exception as e:
            logger.warning(
                "Could not set currency code in PriceFeedService", exc_info=e
            )

        def price_feed_result_handler(price: float):
            if price > 0:
                logger.info(
                    f"{upper_case_currency_code} price feed request returned {price}"
                )
                if is_fiat_currency(upper_case_currency_code):
                    result_handler(MathUtils.round_double(price, 4))
                elif is_crypto_currency(upper_case_currency_code):
                    result_handler(MathUtils.round_double(price, 8))
                else:
                    # should not happen, throw error if it does
                    raise IllegalStateException(
                        f"{upper_case_currency_code} price feed request should not return data for unsupported currency code"
                    )
            else:
                raise IllegalStateException(
                    f"{upper_case_currency_code} price is not available"
                )

        self.price_feed_service.request_price_feed(
            price_feed_result_handler, lambda msg, e: logger.warning(msg, exc_info=e)
        )

    def get_average_bsq_trade_price(self, days: int):
        prices = get_average_price_tuple(
            self.preferences, self.trade_statistics_manager, days
        )
        if prices[0].get_value() == 0 or prices[1].get_value() == 0:
            raise IllegalStateException("average bsq price is not available")
        return prices
