from decimal import Decimal
from typing import TYPE_CHECKING
from typing import Callable, Optional

from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.api.edit_offer_validator import EditOfferValidator
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.currency_util import (
    api_supports_crypto_currency,
    is_crypto_currency,
    is_fiat_currency,
)
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.offer.bisq_v1.mutable_offer_payload_fields import (
    MutableOfferPayloadFields,
)
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.offer.offer_filter_service_result import OfferFilterServiceResult
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.payment.payment_account_util import PaymentAccountUtil
from bisq.core.util.price_util import PriceUtil
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
import grpc_pb2
from bisq.core.offer.offer_util import OfferUtil

if TYPE_CHECKING:
    from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
    from bisq.core.payment.payment_account import PaymentAccount
    from bitcoinj.core.transaction import Transaction
    from bisq.core.user.user import User
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.api.core_context import CoreContext
    from bisq.core.api.core_wallets_service import CoreWalletsService
    from bisq.core.offer.bisq_v1.create_offer_service import CreateOfferService
    from bisq.core.offer.bsq_swap.open_bsq_swap_offer_service import (
        OpenBsqSwapOfferService,
    )
    from bisq.core.offer.offer_book_service import OfferBookService
    from bisq.core.offer.offer_filter_service import OfferFilterService
    from bisq.core.offer.open_offer import OpenOffer
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.offer.offer import Offer

logger = get_logger(__name__)


class CoreOffersService:
    def _to_offer_with_id(self, id: str, is_my_offer: bool) -> "Offer":
        if is_my_offer:
            return self.get_my_offer(id).offer
        else:
            return self.get_offer(id)

    def __init__(
        self,
        core_context: "CoreContext",
        key_ring: "KeyRing",
        core_wallets_service: "CoreWalletsService",
        create_offer_service: "CreateOfferService",
        offer_book_service: "OfferBookService",
        offer_filter_service: "OfferFilterService",
        open_offer_manager: "OpenOfferManager",
        open_bsq_swap_offer_service: "OpenBsqSwapOfferService",
        offer_util: "OfferUtil",
        price_feed_service: "PriceFeedService",
        user: "User",
    ):
        self.core_context = core_context
        self.key_ring = key_ring
        self.core_wallets_service = core_wallets_service
        self.create_offer_service = create_offer_service
        self.offer_book_service = offer_book_service
        self.offer_filter_service = offer_filter_service
        self.open_offer_manager = open_offer_manager
        self.open_bsq_swap_offer_service = open_bsq_swap_offer_service
        self.offer_util = offer_util
        self.price_feed_service = price_feed_service
        self.user = user

    def is_fiat_offer(self, id: str, is_my_offer: bool) -> bool:
        offer = self._to_offer_with_id(id, is_my_offer)
        return OfferUtil.is_fiat_offer(offer)

    def is_altcoin_offer(self, id: str, is_my_offer: bool) -> bool:
        offer = self._to_offer_with_id(id, is_my_offer)
        return OfferUtil.is_altcoin_offer(offer)

    def is_bsq_swap_offer(self, id: str, is_my_offer: bool) -> bool:
        offer = self._to_offer_with_id(id, is_my_offer)
        return offer.is_bsq_swap_offer

    def get_offer(self, id: str) -> Optional["Offer"]:
        offer = self.find_available_offer(id)
        if offer is None:
            raise NotFoundException(f"offer with id '{id}' not found")
        return offer

    def find_available_offer(self, id: str) -> Optional["Offer"]:
        for o in self.offer_book_service.get_offers():
            if o.id == id:
                inquiry_result = self.offer_filter_service.can_take_offer(
                    o, self.key_ring, False, self.core_context.is_api_user
                )
                if inquiry_result.is_valid:
                    return o
                else:
                    raise IllegalStateException(
                        f"Offer id '{id}' is not available to take: {inquiry_result.name}"
                    )
        return None

    def get_my_offer(self, id: str) -> "OpenOffer":
        open_offer = self.find_my_open_offer(id)
        if open_offer is None:
            raise NotFoundException(f"offer with id '{id}' not found")
        return open_offer

    def find_my_open_offer(self, id: str) -> Optional["OpenOffer"]:
        offers = self.open_offer_manager.get_observable_list()
        return next(
            (
                o
                for o in offers
                if o.get_id() == id and o.get_offer().is_my_offer(self.key_ring)
            ),
            None,
        )

    def get_bsq_swap_offer(self, id: str) -> "Offer":
        offer = self.find_available_bsq_swap_offer(id)
        if offer is None:
            raise NotFoundException(f"offer with id '{id}' not found")
        return offer

    def find_available_bsq_swap_offer(self, id: str) -> Optional["Offer"]:
        for o in self.offer_book_service.get_offers():
            if o.id == id:
                inquiry_result = self.offer_filter_service.can_take_offer(
                    o, self.key_ring, True, self.core_context.is_api_user
                )
                if inquiry_result.is_valid:
                    return o
                else:
                    raise IllegalStateException(
                        f"Offer id '{id}' is not available to take: {inquiry_result.name}"
                    )
        return None

    def get_my_bsq_swap_offer(self, id: str) -> "Offer":
        offer = self.find_my_bsq_swap_offer(id)
        if offer is None:
            raise NotFoundException(f"offer with id '{id}' not found")
        return offer

    def find_my_bsq_swap_offer(self, id: str) -> Optional["Offer"]:
        offers = self.offer_book_service.get_offers()
        return next(
            (
                o
                for o in offers
                if o.id == id and o.is_my_offer(self.key_ring) and o.is_bsq_swap_offer
            ),
            None,
        )

    def get_bsq_swap_offers(self, direction: str) -> list["Offer"]:
        offers = self.offer_book_service.get_offers()
        cleaned_direction = direction.strip().casefold()
        filtered = [
            o
            for o in offers
            if not o.is_my_offer(self.key_ring)
            and o.direction.name.casefold() == cleaned_direction
            and o.is_bsq_swap_offer
        ]
        return sorted(filtered, key=self.price_comparator(direction, False))

    def get_offers(self, direction: str, currency_code: str) -> list["Offer"]:
        upper_case_currency_code = currency_code.upper()
        is_fiat = is_fiat_currency(upper_case_currency_code)

        if is_fiat:
            offers = self.offer_book_service.get_offers()
            return sorted(
                (
                    o
                    for o in offers
                    if self._offer_matches_direction_and_currency(
                        o, direction, upper_case_currency_code
                    )
                ),
                key=self.price_comparator(direction, True),
            )
        else:
            # In fiat offers, the baseCurrencyCode=BTC, counterCurrencyCode=FiatCode.
            # In altcoin offers, baseCurrencyCode=AltcoinCode, counterCurrencyCode=BTC.
            # This forces an extra filtering step below:  get all BTC offers,
            # then filter on the currencyCode param (the altcoin code).
            if api_supports_crypto_currency(upper_case_currency_code):
                offers = self.offer_book_service.get_offers()

                return sorted(
                    (
                        o
                        for o in offers
                        if self._offer_matches_direction_and_currency(
                            o, direction, "BTC"
                        )
                        and o.base_currency_code.upper() == upper_case_currency_code
                    ),
                    key=self.price_comparator(direction, False),
                )
            else:
                raise IllegalArgumentException(
                    f"api does not support the '{upper_case_currency_code}' crypto currency"
                )

    def get_my_offers(self, direction: str, currency_code: str) -> list["OpenOffer"]:
        upper_case_currency_code = currency_code.upper()
        is_fiat = is_fiat_currency(upper_case_currency_code)

        if is_fiat:
            offers = self.open_offer_manager.get_observable_list()
            filtered = [
                o
                for o in offers
                if o.get_offer().is_my_offer(self.key_ring)
                and self._offer_matches_direction_and_currency(
                    o.get_offer(), direction, upper_case_currency_code
                )
            ]
            return sorted(
                filtered, key=self.open_offer_price_comparator(direction, True)
            )
        else:
            # In fiat offers, the baseCurrencyCode=BTC, counterCurrencyCode=FiatCode.
            # In altcoin offers, baseCurrencyCode=AltcoinCode, counterCurrencyCode=BTC.
            # This forces an extra filtering step below:  get all BTC offers,
            # then filter on the currencyCode param (the altcoin code).
            if api_supports_crypto_currency(upper_case_currency_code):
                offers = self.open_offer_manager.get_observable_list()
                filtered = [
                    o
                    for o in offers
                    if o.get_offer().is_my_offer(self.key_ring)
                    and self._offer_matches_direction_and_currency(
                        o.get_offer(), direction, "BTC"
                    )
                    and o.get_offer().base_currency_code.upper()
                    == upper_case_currency_code
                ]
                return sorted(
                    filtered, key=self.open_offer_price_comparator(direction, False)
                )
            else:
                raise IllegalArgumentException(
                    f"api does not support the '{upper_case_currency_code}' crypto currency"
                )

    def get_my_bsq_swap_offers(self, direction: str) -> list["Offer"]:
        offers = self.offer_book_service.get_offers()
        # TODO: maybe convert direction str to enum then compare directly for faster results ?
        cleaned_direction = direction.strip().casefold()
        filtered = [
            o
            for o in offers
            if o.is_my_offer(self.key_ring)
            and o.direction.name.casefold() == cleaned_direction
            and o.is_bsq_swap_offer
        ]
        return sorted(filtered, key=self.price_comparator(direction, False))

    def get_my_open_bsq_swap_offer(self, id: str) -> "OpenOffer":
        open_offer = self.open_offer_manager.get_open_offer_by_id(id)
        if (
            open_offer is not None
            and open_offer.get_offer().is_my_offer(self.key_ring)
            and open_offer.get_offer().is_bsq_swap_offer
        ):
            return open_offer
        raise NotFoundException(f"openoffer with id '{id}' not found")

    def get_my_open_offer(self, id: str) -> "OpenOffer":
        open_offer = self.open_offer_manager.get_open_offer_by_id(id)
        if open_offer is not None and open_offer.get_offer().is_my_offer(self.key_ring):
            return open_offer
        raise NotFoundException(f"offer with id '{id}' not found")

    def is_my_offer(self, offer: "Offer") -> bool:
        return offer.is_my_offer(self.key_ring)

    def create_and_place_bsq_swap_offer(
        self,
        direction_as_string: str,
        amount_as_long: int,
        min_amount_as_long: int,
        price_as_string: str,
        result_handler: Callable[["Offer"], None],
    ):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        currency_code = "BSQ"
        offer_id = OfferUtil.get_random_offer_id()
        direction = OfferDirection[direction_as_string.upper()]
        amount = Coin.value_of(amount_as_long)
        min_amount = (
            amount if min_amount_as_long == 0 else Coin.value_of(min_amount_as_long)
        )
        price = Price.value_of(
            currency_code, self._price_string_to_long(price_as_string, currency_code)
        )

        self.open_bsq_swap_offer_service.request_new_offer(
            offer_id,
            direction,
            amount,
            min_amount,
            price,
            lambda offer: self._place_bsq_swap_offer(
                offer, lambda: result_handler(offer)
            ),
        )

    def create_and_place_offer(
        self,
        currency_code: str,
        direction_as_string: str,
        price_as_string: str,
        use_market_based_price: bool,
        market_price_margin: float,
        amount_as_long: int,
        min_amount_as_long: int,
        buyer_security_deposit_pct: float,
        trigger_price: str,
        payment_account_id: str,
        maker_fee_currency_code: str,
        result_handler: Callable[["Offer"], None],
    ):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()
        self.offer_util.maybe_set_fee_payment_currency_preference(
            maker_fee_currency_code
        )

        payment_account = self.user.get_payment_account(payment_account_id)
        if payment_account is None:
            raise IllegalArgumentException(
                f"payment account with id {payment_account_id} not found"
            )

        upper_case_currency_code = currency_code.upper()
        offer_id = OfferUtil.get_random_offer_id()
        direction = OfferDirection[direction_as_string.upper()]
        price = Price.value_of(
            upper_case_currency_code,
            self._price_string_to_long(price_as_string, upper_case_currency_code),
        )
        amount = Coin.value_of(amount_as_long)
        min_amount = (
            amount if min_amount_as_long == 0 else Coin.value_of(min_amount_as_long)
        )
        use_default_tx_fee = Coin.ZERO()

        # Almost ready to call createOfferService.createAndGetOffer(), but first:
        #
        # For the buyer security deposit parameter, API clients pass a double as a
        # percent literal, e.g., #.## (%), where "1.00 means 1% of the trade amount".
        # Desktop (UI) clients convert the percent literal string input before passing
        # a representation of a pct as a decimal, e.g., 0.##.
        # See bisq.desktop.main.offer.bisq_v1.MutableOfferDataModel, where
        # "Pct value of buyer security deposit, e.g., 0.01 means 1% of trade amount."
        #
        # The API client's percent literal is transformed now, to make sure the double
        # passed into createOfferService.createAndGetOffer() is correctly scaled.
        scaled_buyer_security_deposit_pct = MathUtils.exact_multiply(
            buyer_security_deposit_pct, 0.01
        )

        offer = self.create_offer_service.create_and_get_offer(
            offer_id,
            direction,
            upper_case_currency_code,
            amount,
            min_amount,
            price,
            use_default_tx_fee,
            use_market_based_price,
            MathUtils.exact_multiply(market_price_margin, 0.01),
            scaled_buyer_security_deposit_pct,
            payment_account,
        )

        self._verify_payment_account_is_valid_for_new_offer(offer, payment_account)

        # We don't support atm funding from external wallet to keep it simple.
        use_savings_wallet = True
        self._place_offer(
            offer,
            scaled_buyer_security_deposit_pct,
            trigger_price,
            use_savings_wallet,
            lambda transaction: result_handler(offer),
        )

    # Edit a placed offer.
    def edit_offer(
        self,
        offer_id: str,
        edited_price: str,
        edited_use_market_based_price: bool,
        edited_market_price_margin: float,
        edited_trigger_price: str,
        edited_enable: int,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ):
        open_offer = self.get_my_open_offer(offer_id)
        validator = EditOfferValidator(
            open_offer,
            edited_price,
            edited_use_market_based_price,
            edited_market_price_margin,
            edited_trigger_price,
            edited_enable,
            edit_type,
        ).validate()
        logger.info(str(validator))
        current_offer_state = open_offer.state
        # Client sent (sint32) editedEnable, not a bool (with default=false).
        # If editedEnable = -1, do not change current state
        # If editedEnable =  0, set state = AVAILABLE
        # If editedEnable =  1, set state = DEACTIVATED
        new_offer_state = (
            current_offer_state
            if edited_enable < 0
            else (
                OpenOfferState.AVAILABLE
                if edited_enable > 0
                else OpenOfferState.DEACTIVATED
            )
        )
        edited_payload = self._get_merged_offer_payload(
            validator,
            open_offer,
            edited_price,
            edited_market_price_margin,
            edit_type,
        )
        edited_offer = Offer(edited_payload)
        self.price_feed_service.currency_code = open_offer.get_offer().currency_code
        edited_offer.price_feed_service = self.price_feed_service
        edited_offer.state = OpenOfferState.AVAILABLE
        self.open_offer_manager.edit_open_offer_start(
            open_offer,
            lambda: logger.info(f"EditOpenOfferStart: offer {open_offer.get_id()}"),
            logger.error,
        )
        trigger_price_as_long = PriceUtil.get_market_price_as_long(
            edited_trigger_price, edited_offer.currency_code
        )
        self.open_offer_manager.edit_open_offer_publish(
            edited_offer,
            trigger_price_as_long,
            new_offer_state,
            lambda: logger.info(f"EditOpenOfferPublish: offer {open_offer.get_id()}"),
            logger.error,
        )

    def cancel_offer(self, id: str):
        open_offer = self.get_my_offer(id)
        self.open_offer_manager.remove_offer(
            open_offer.get_offer(),
            lambda: None,
            logger.error,
        )

    def _place_bsq_swap_offer(self, offer: "Offer", result_handler: Callable[[], None]):
        self.open_bsq_swap_offer_service.place_bsq_swap_offer(
            offer,
            result_handler,
            logger.error,
        )

        if offer.error_message is not None:
            raise IllegalStateException(offer.error_message)

    def _place_offer(
        self,
        offer: "Offer",
        buyer_security_deposit_pct: float,
        trigger_price: str,
        use_savings_wallet: bool,
        result_handler: Callable[["Transaction"], None],
    ):
        trigger_price_as_long = PriceUtil.get_market_price_as_long(
            trigger_price, offer.currency_code
        )
        self.open_offer_manager.place_offer(
            offer,
            buyer_security_deposit_pct,
            use_savings_wallet,
            False,
            trigger_price_as_long,
            result_handler,
            logger.error,
        )

        if offer.error_message is not None:
            raise IllegalStateException(offer.error_message)

    def _get_merged_offer_payload(
        self,
        edit_offer_validator: "EditOfferValidator",
        open_offer: "OpenOffer",
        edited_price: str,
        edited_market_price_margin: float,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ) -> "OfferPayload":
        # API supports editing (1) price, OR (2) marketPriceMargin & useMarketBasedPrice
        # OfferPayload fields.  API does not support editing payment acct or currency
        # code fields.  Note: triggerPrice isDeactivated fields are in OpenOffer, not
        # in OfferPayload.
        offer = open_offer.get_offer()
        currency_code = offer.currency_code
        is_using_mkt_price_margin = (
            edit_offer_validator.is_editing_use_mkt_price_margin_flag(offer, edit_type)
        )
        is_editing_fixed_price = edit_type in [
            grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_ONLY,
            grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_AND_ACTIVATION_STATE,
        ]

        if is_editing_fixed_price:
            edited_fixed_price = Price.value_of(
                currency_code, self._price_string_to_long(edited_price, currency_code)
            )
        else:
            # When is_using_mkt_price_margin=True, (fixed) price must be set to 0 on the server.
            # The client, however, still must show the calculated price when
            # is_using_mkt_price_margin=True.
            edited_fixed_price = (
                Price.value_of(currency_code, 0)
                if is_using_mkt_price_margin
                else offer.get_price()
            )

        # If is_using_mkt_price_margin=True , throw exception if new fixed-price != 0.
        # If is_using_mkt_price_margin=False, throw exception if new fixed-price == 0.
        if is_using_mkt_price_margin and edited_fixed_price.value != 0:
            raise IllegalStateException(
                f"Fixed price on mkt price margin based offer {offer.id} must be set to 0 in server."
            )
        elif not is_using_mkt_price_margin:
            assert (
                edited_fixed_price is not None
            ), "edited_fixed_price cannot be None here"
            if edited_fixed_price.value == 0:
                raise IllegalStateException(
                    f"Fixed price on fixed price offer {offer.id} cannot be 0."
                )

        is_editing_mkt_price_margin = edit_offer_validator.is_editing_mkt_price_margin(
            edit_type
        )
        new_market_price_margin = (
            MathUtils.exact_multiply(edited_market_price_margin, 0.01)
            if is_editing_mkt_price_margin
            else offer.market_price_margin
        )

        assert edited_fixed_price is not None, "edited_fixed_price cannot be None here"
        mutable_offer_payload_fields = MutableOfferPayloadFields(
            edited_fixed_price.value,
            new_market_price_margin if is_using_mkt_price_margin else 0.00,
            is_using_mkt_price_margin,
            offer.base_currency_code,
            offer.counter_currency_code,
            offer.payment_method.id,
            offer.maker_payment_account_id,
            offer.max_trade_limit.value,
            offer.max_trade_period,
            offer.country_code,
            offer.accepted_country_codes,
            offer.bank_id,
            offer.accepted_bank_ids,
            offer.extra_data_map,
        )
        logger.info(f"Merging OfferPayload with {mutable_offer_payload_fields}")
        return self.offer_util.get_merged_offer_payload(
            open_offer, mutable_offer_payload_fields
        )

    def _verify_payment_account_is_valid_for_new_offer(
        self, offer: "Offer", payment_account: "PaymentAccount"
    ):
        if not PaymentAccountUtil.is_payment_account_valid_for_offer(
            offer, payment_account
        ):
            error = f"cannot create {offer.counter_currency_code} offer with payment account {payment_account.id}"
            raise IllegalStateException(error)

    def _offer_matches_direction_and_currency(
        self, offer: "Offer", direction: str, currency_code: str
    ) -> bool:
        is_direction_match = offer.direction.name.casefold() == direction.casefold()
        is_currency_match = (
            offer.counter_currency_code.casefold() == currency_code.casefold()
        )
        return is_direction_match and is_currency_match

    def open_offer_price_comparator(
        self, direction: str, is_fiat: bool
    ) -> Callable[["OpenOffer"], float]:
        # TODO: check if it yields same result as java
        # A buyer probably wants to see sell orders in price ascending order.
        # A seller probably wants to see buy orders in price descending order.
        if is_fiat:
            direction_is_buy = (
                direction.strip().casefold() == OfferDirection.BUY.name.casefold()
            )
            return lambda offer: (
                -offer.get_offer().get_price()
                if direction_is_buy
                else offer.get_offer().get_price()
            )
        else:
            direction_is_sell = (
                direction.strip().casefold() == OfferDirection.SELL.name.casefold()
            )
            return lambda offer: (
                -offer.get_offer().get_price()
                if direction_is_sell
                else offer.get_offer().get_price()
            )

    def price_comparator(
        self, direction: str, is_fiat: bool
    ) -> Callable[["Offer"], float]:
        # TODO: check if it yields same result as java
        # A buyer probably wants to see sell orders in price ascending order.
        # A seller probably wants to see buy orders in price descending order.
        if is_fiat:
            direction_is_buy = (
                direction.strip().casefold() == OfferDirection.BUY.name.casefold()
            )
            return lambda offer: (
                -offer.get_price() if direction_is_buy else offer.get_price()
            )
        else:
            direction_is_sell = (
                direction.strip().casefold() == OfferDirection.SELL.name.casefold()
            )
            return lambda offer: (
                -offer.get_price() if direction_is_sell else offer.get_price()
            )

    def _price_string_to_long(self, price_as_string: str, currency_code: str) -> int:
        if is_crypto_currency(currency_code):
            precision = Altcoin.SMALLEST_UNIT_EXPONENT
        else:
            precision = Fiat.SMALLEST_UNIT_EXPONENT
        price_as_float = float(Decimal(price_as_string))
        scaled = MathUtils.scale_up_by_power_of_10(price_as_float, precision)
        return MathUtils.round_double_to_long(scaled)
