from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.util.math_utils import MathUtils
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.currency_util import is_crypto_currency, is_fiat_currency
from bisq.core.util.average_price_util import get_average_price_tuple

if TYPE_CHECKING:
    from bisq.core.user.user_context import UserContext


class CorePriceService:

    def _is_currency_code(self, currency_code: str) -> bool:
        return is_fiat_currency(currency_code) or is_crypto_currency(currency_code)

    def get_market_price(
        self,
        user_context: "UserContext",
        currency_code: str,
        result_handler: Callable[[float], None],
    ) -> float:
        c = user_context.global_container
        upper_case_currency_code = currency_code.upper()

        if not self._is_currency_code(upper_case_currency_code):
            raise IllegalStateException(
                f"{upper_case_currency_code} is not a valid currency code"
            )

        if not c.price_feed_service.has_prices:
            raise IllegalStateException("price feed service has no prices")

        try:
            c.price_feed_service.currency_code = upper_case_currency_code
        except Exception as e:
            user_context.logger.warning(
                "Could not set currency code in PriceFeedService", exc_info=e
            )

        def price_feed_result_handler(price: float):
            if price > 0:
                user_context.logger.info(
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

        c.price_feed_service.request_price_feed(
            price_feed_result_handler,
            lambda msg, e: user_context.logger.warning(msg, exc_info=e),
        )

    def get_average_bsq_trade_price(self, user_context: "UserContext", days: int):
        c = user_context.global_container
        prices = get_average_price_tuple(
            c.preferences, c.trade_statistics_manager, days
        )
        if prices[0].get_value() == 0 or prices[1].get_value() == 0:
            raise IllegalStateException("average bsq price is not available")
        return prices
