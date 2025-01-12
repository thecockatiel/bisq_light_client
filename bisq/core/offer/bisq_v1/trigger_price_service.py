from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.core.locale.res import Res
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.provider.mempool.fee_validation_status import FeeValidationStatus
from utils.data import ObservableChangeEvent, SimpleProperty
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.offer.offer_direction import OfferDirection
from bitcoinj.base.utils.fiat import Fiat

if TYPE_CHECKING:
    from bisq.core.provider.mempool.tx_validator import TxValidator
    from bisq.core.provider.price.market_price import MarketPrice
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.open_offer import OpenOffer
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.mempool.mempool_service import MempoolService
    from bisq.core.provider.price.price_feed_service import PriceFeedService


logger = get_logger(__name__)


class TriggerPriceService:
    def __init__(
        self,
        p2p_service: "P2PService",
        open_offer_manager: "OpenOfferManager",
        mempool_service: "MempoolService",
        price_feed_service: "PriceFeedService",
    ):
        self.p2p_service = p2p_service
        self.open_offer_manager = open_offer_manager
        self.mempool_service = mempool_service
        self.price_feed_service = price_feed_service
        self.open_offers_by_currency = dict[str, set["OpenOffer"]]()
        self.offer_disabled_handler: Optional[Callable[[str], None]] = None
        self.update_counter = SimpleProperty(0)

    def on_all_services_initialized(
        self,
        offer_disabled_handler: Callable[[str], None],
    ):
        self.offer_disabled_handler = offer_disabled_handler
        if self.p2p_service.is_bootstrapped:
            self._on_bootstrap_complete()
        else:

            class Listener(BootstrapListener):
                def on_data_received(self_):
                    self._on_bootstrap_complete()

            self.p2p_service.add_p2p_service_listener(Listener())

    def _on_bootstrap_complete(self) -> None:
        def on_open_offer_change(e: ObservableChangeEvent["OpenOffer"]):
            if e.added_elements:
                self._on_added_open_offers(e.added_elements)
            if e.removed_elements:
                self._on_removed_open_offers(e.removed_elements)

        self.open_offer_manager.get_observable_list().add_listener(on_open_offer_change)

        self._on_added_open_offers(self.open_offer_manager.get_observable_list())

        self.price_feed_service.update_counter_property.add_listener(
            lambda e: self._on_price_feed_changed(False)
        )
        self._on_price_feed_changed(True)

    def _on_price_feed_changed(self, bootstrapping: bool) -> None:
        for market_price in filter(
            lambda mp: mp is not None
            and mp.currency_code in self.open_offers_by_currency,
            map(
                self.price_feed_service.get_market_price,
                self.open_offers_by_currency.keys(),
            ),
        ):
            for open_offer in self.open_offers_by_currency[market_price.currency_code]:
                if not open_offer.is_deactivated:
                    self._check_price_threshold(market_price, open_offer)
                    if not bootstrapping:
                        self._maybe_check_offer_fee(open_offer)

    @staticmethod
    def was_triggered(market_price: "MarketPrice", open_offer: "OpenOffer") -> bool:
        price = open_offer.get_offer().get_price()
        if price is None or market_price is None:
            return False

        currency_code = open_offer.get_offer().currency_code
        crypto_currency = is_crypto_currency(currency_code)
        smallest_unit_exponent = (
            Altcoin.SMALLEST_UNIT_EXPONENT
            if crypto_currency
            else Fiat.SMALLEST_UNIT_EXPONENT
        )
        market_price_as_long = MathUtils.round_double_to_long(
            MathUtils.scale_up_by_power_of_10(
                market_price.price, smallest_unit_exponent
            )
        )
        trigger_price = open_offer.trigger_price
        if trigger_price <= 0:
            return False

        direction = open_offer.get_offer().direction
        is_sell_offer = direction == OfferDirection.SELL
        condition = (is_sell_offer and not crypto_currency) or (
            not is_sell_offer and crypto_currency
        )
        if condition:
            return market_price_as_long < trigger_price
        else:
            return market_price_as_long > trigger_price

    def _check_price_threshold(
        self, market_price: "MarketPrice", open_offer: "OpenOffer"
    ) -> None:
        offer = open_offer.get_offer()
        if offer.is_bsq_swap_offer:
            return

        if self.was_triggered(market_price, open_offer):
            currency_code = offer.currency_code
            smallest_unit_exponent = (
                Altcoin.SMALLEST_UNIT_EXPONENT
                if is_crypto_currency(currency_code)
                else Fiat.SMALLEST_UNIT_EXPONENT
            )
            trigger_price = open_offer.trigger_price

            logger.info(
                f"Market price exceeded the trigger price of the open offer.\n"
                f"We deactivate the open offer with ID {offer.short_id}.\n"
                f"Currency: {currency_code};\n"
                f"Offer direction: {offer.direction};\n"
                f"Market price: {market_price.price};\n"
                f"Trigger price: {MathUtils.scale_down_by_power_of_10(trigger_price, smallest_unit_exponent)}"
            )
            self._deactivate_open_offer(
                open_offer,
                Res.get("openOffer.triggered", open_offer.get_offer().short_id),
            )

    def _maybe_check_offer_fee(self, open_offer: "OpenOffer") -> None:
        offer = open_offer.get_offer()
        if offer.is_bsq_swap_offer:
            return

        if open_offer.state == OpenOfferState.AVAILABLE:
            # check the offer fee if it has not been done before
            offer_payload = offer.offer_payload
            if offer_payload is None:
                raise ValueError("Offer payload is None")
            if (
                open_offer.fee_validation_status == FeeValidationStatus.NOT_CHECKED_YET
                and self.mempool_service.can_request_be_made(offer_payload)
            ):

                def on_validation(tx_validator: "TxValidator"):
                    open_offer.fee_validation_status = tx_validator.status
                    if open_offer.fee_validation_status.fails:
                        self._deactivate_open_offer(
                            open_offer,
                            Res.get(
                                "openOffer.deactivated.feeValidationIssue",
                                open_offer.get_offer().short_id,
                                open_offer.fee_validation_status.name,
                            ),
                        )

                self.mempool_service.validate_offer_maker_tx(
                    offer_payload,
                    on_validation,
                )

    def _deactivate_open_offer(self, open_offer: "OpenOffer", message: str) -> None:
        self.open_offer_manager.deactivate_open_offer(
            open_offer, lambda: None, lambda e: None
        )
        logger.info(message)
        if self.offer_disabled_handler is not None:
            self.offer_disabled_handler(message)  # shows notification on screen
        # tells the UI layer (Open Offers View) to update its contents
        self.update_counter.set(self.update_counter.get() + 1)

    def _on_added_open_offers(self, open_offers: list["OpenOffer"]) -> None:
        for open_offer in open_offers:
            currency_code = open_offer.get_offer().currency_code
            if currency_code not in self.open_offers_by_currency:
                self.open_offers_by_currency[currency_code] = set()
            self.open_offers_by_currency[currency_code].add(open_offer)

            market_price = self.price_feed_service.get_market_price(
                open_offer.get_offer().currency_code
            )
            if market_price is not None:
                self._check_price_threshold(market_price, open_offer)

    def _on_removed_open_offers(self, open_offers: list["OpenOffer"]) -> None:
        for open_offer in open_offers:
            currency_code = open_offer.get_offer().currency_code
            if currency_code in self.open_offers_by_currency:
                offer_set = self.open_offers_by_currency[currency_code]
                if open_offer.is_canceled:
                    offer_set.discard(open_offer)
                if not offer_set:
                    del self.open_offers_by_currency[currency_code]
