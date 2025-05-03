from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING

from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import (
    get_currency_pair,
    is_crypto_currency,
    get_currency_name_by_code,
)
from bisq.core.locale.res import Res
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.notifications.mobile_message import MobileMessage
from bisq.core.notifications.mobile_message_type import MobileMessageType
from bisq.core.util.formatting_util import FormattingUtils
from bitcoinj.base.utils.fiat import Fiat


if TYPE_CHECKING:
    from bisq.core.notifications.mobile_notification_service import (
        MobileNotificationService,
    )
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.user.user import User


class PriceAlert:

    def __init__(
        self,
        price_feed_service: "PriceFeedService",
        mobile_notification_service: "MobileNotificationService",
        user: "User",
    ):
        self.logger = get_ctx_logger(__name__)
        self.price_feed_service = price_feed_service
        self.user = user
        self.mobile_notification_service = mobile_notification_service

    def on_all_services_initialized(self):
        self.price_feed_service.update_counter_property.add_listener(self._update)

    def shut_down(self):
        self.price_feed_service.update_counter_property.remove_listener(self._update)

    def _update(self, *args, **kwargs):
        if self.user.price_alert_filter:
            filter = self.user.price_alert_filter
            currency_code = filter.currency_code
            market_price = self.price_feed_service.get_market_price(currency_code)
            if market_price:
                exp = (
                    Altcoin.SMALLEST_UNIT_EXPONENT
                    if is_crypto_currency(currency_code)
                    else Fiat.SMALLEST_UNIT_EXPONENT
                )
                price_as_double = market_price.price
                price_as_long = MathUtils.round_double_to_long(
                    MathUtils.scale_up_by_power_of_10(price_as_double, exp)
                )
                currency_name = get_currency_name_by_code(currency_code)

                if price_as_long > filter.high or price_as_long < filter.low:
                    msg = Res.get(
                        "account.notifications.priceAlert.message.msg",
                        currency_name,
                        FormattingUtils.format_market_price(
                            price_as_double, currency_code
                        ),
                        get_currency_pair(currency_code),
                    )

                    message = MobileMessage(
                        title=Res.get(
                            "account.notifications.priceAlert.message.title",
                            currency_name,
                        ),
                        message=msg,
                        mobile_message_type=MobileMessageType.PRICE,
                    )

                    try:
                        self.mobile_notification_service.send_message(message)

                        # If an alert got triggered we remove the filter.
                        self.user.remove_price_alert_filter()
                    except Exception as e:
                        self.logger.error(e)

    @staticmethod
    def get_test_msg() -> "MobileMessage":
        currency_code = "USD"
        currency_name = get_currency_name_by_code(currency_code)
        msg = Res.get(
            "account.notifications.priceAlert.message.msg",
            currency_name,
            "6023.34",
            "BTC/USD",
        )
        return MobileMessage(
            title=Res.get(
                "account.notifications.priceAlert.message.title", currency_name
            ),
            message=msg,
            mobile_message_type=MobileMessageType.PRICE,
        )
