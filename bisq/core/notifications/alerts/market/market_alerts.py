from typing import TYPE_CHECKING
import uuid

from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import (
    get_currency_pair,
    is_crypto_currency as util_is_crypto_currency,
    is_fiat_currency as util_is_fiat_currency,
)
from bisq.core.locale.res import Res
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.notifications.alerts.market.market_alert_filter import MarketAlertFilter
from bisq.core.notifications.mobile_message import MobileMessage
from bisq.core.notifications.mobile_message_type import MobileMessageType
from bisq.core.offer.offer_book_changed_listener import OfferBookChangedListener
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.util.formatting_util import FormattingUtils
from bitcoinj.base.utils.fiat import Fiat

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.notifications.mobile_notification_service import (
        MobileNotificationService,
    )
    from bisq.core.offer.offer_book_service import OfferBookService
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.user.user import User

logger = get_logger(__name__)


class MarketAlerts:

    def __init__(
        self,
        offer_book_service: "OfferBookService",
        mobile_notification_service: "MobileNotificationService",
        user: "User",
        price_feed_service: "PriceFeedService",
        key_ring: "KeyRing",
    ):
        self.offer_book_service = offer_book_service
        self.mobile_notification_service = mobile_notification_service
        self.user = user
        self.price_feed_service = price_feed_service
        self.key_ring = key_ring

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self):
        class Listener(OfferBookChangedListener):
            def on_added(self_, offer: "Offer"):
                self._on_offer_added(offer)

            def on_removed(self, offer: "Offer"):
                pass

        self.offer_book_service.add_offer_book_changed_listener(Listener())
        self._apply_filter_on_all_offers()

    def add_market_alert_filter(self, filter: "MarketAlertFilter"):
        self.user.add_market_alert_filter(filter)
        self._apply_filter_on_all_offers()

    def remove_market_alert_filter(self, filter: "MarketAlertFilter"):
        self.user.remove_market_alert_filter(filter)

    def get_market_alert_filters(self) -> list["MarketAlertFilter"]:
        return self.user.market_alert_filters

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _apply_filter_on_all_offers(self):
        for offer in self.offer_book_service.get_offers():
            self._on_offer_added(offer)

    # We combine the offer ID and the price (either as % price or as fixed price) to get also updates for edited offers
    # % price get multiplied by 10000 to have 0.12% be converted to 12. For fixed price we have precision of 8 for
    # altcoins and precision of 4 for fiat.
    def _get_alert_id(self, offer: "Offer"):
        price = (
            offer.market_price_margin * 10000
            if offer.is_use_market_based_price
            else offer.fixed_price
        )
        price_string = str(int(price))
        return f"{offer.id}|{price_string}"

    def _on_offer_added(self, offer: "Offer"):
        currency_code = offer.currency_code
        market_price = self.price_feed_service.get_market_price(currency_code)
        offer_price = offer.get_price()

        if market_price and offer_price:
            is_sell_offer = offer.direction == OfferDirection.SELL
            short_offer_id = offer.short_id
            is_fiat_currency = util_is_fiat_currency(currency_code)
            alert_id = self._get_alert_id(offer)

            for market_alert_filter in self.user.market_alert_filters:
                if (
                    offer.is_my_offer(self.key_ring)
                    or offer.payment_method
                    != market_alert_filter.payment_account.payment_method
                    or market_alert_filter.contains_alert_id(alert_id)
                ):
                    continue

                trigger_value = market_alert_filter.trigger_value
                is_trigger_for_buy_offer = market_alert_filter.is_buy_offer
                market_price_value = market_price.price

                precision = (
                    Altcoin.SMALLEST_UNIT_EXPONENT
                    if util_is_crypto_currency(currency_code)
                    else Fiat.SMALLEST_UNIT_EXPONENT
                )
                market_price_scaled = MathUtils.scale_up_by_power_of_10(
                    market_price_value, precision
                )

                ratio = (1 - (offer_price.value / market_price_scaled)) * 10000

                if (is_fiat_currency and is_sell_offer) or (
                    not is_fiat_currency and not is_sell_offer
                ):
                    ratio *= -1

                if ratio > trigger_value:
                    continue

                if (not is_sell_offer and is_trigger_for_buy_offer) or (
                    is_sell_offer and not is_trigger_for_buy_offer
                ):
                    direction = (
                        Res.get("shared.sell")
                        if is_sell_offer
                        else Res.get("shared.buy")
                    )

                    if is_fiat_currency:
                        if is_sell_offer:
                            market_dir = (
                                Res.get(
                                    "account.notifications.marketAlert.message.msg.above"
                                )
                                if ratio > 0
                                else Res.get(
                                    "account.notifications.marketAlert.message.msg.below"
                                )
                            )
                        else:
                            market_dir = (
                                Res.get(
                                    "account.notifications.marketAlert.message.msg.above"
                                )
                                if ratio < 0
                                else Res.get(
                                    "account.notifications.marketAlert.message.msg.below"
                                )
                            )
                    else:
                        if is_sell_offer:
                            market_dir = (
                                Res.get(
                                    "account.notifications.marketAlert.message.msg.above"
                                )
                                if ratio < 0
                                else Res.get(
                                    "account.notifications.marketAlert.message.msg.below"
                                )
                            )
                        else:
                            market_dir = (
                                Res.get(
                                    "account.notifications.marketAlert.message.msg.above"
                                )
                                if ratio > 0
                                else Res.get(
                                    "account.notifications.marketAlert.message.msg.below"
                                )
                            )

                    ratio = abs(ratio) / 10000
                    msg = Res.get(
                        "account.notifications.marketAlert.message.msg",
                        direction,
                        get_currency_pair(currency_code),
                        FormattingUtils.format_price(offer_price),
                        FormattingUtils.format_to_percent_with_symbol(ratio),
                        market_dir,
                        Res.get(offer.payment_method.id),
                        short_offer_id,
                    )

                    message = MobileMessage(
                        Res.get("account.notifications.marketAlert.message.title"),
                        msg,
                        MobileMessageType.MARKET,
                        short_offer_id,
                    )

                    try:
                        was_sent = self.mobile_notification_service.send_message(
                            message
                        )
                        if was_sent:
                            # In case we have disabled alerts wasSent is false and we do not
                            # persist the offer
                            market_alert_filter.add_alert_id(alert_id)
                            self.user.request_persistence()
                    except Exception as e:
                        logger.error(f"Error sending notification: {e}", exc_info=e)

    @staticmethod
    def get_test_msg():
        short_id = str(uuid.uuid4())[:8]
        return MobileMessage(
            Res.get("account.notifications.marketAlert.message.title"),
            "A new 'sell BTC/USD' offer with price 6019.2744 (5.36% below market price) and payment method 'Perfect Money' was published to the Bisq offerbook.\nOffer ID: wygiaw.",
            MobileMessageType.MARKET,
            short_id,
        )
