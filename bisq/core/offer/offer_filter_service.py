from collections import defaultdict
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.account.witness.account_age_witness_service import (
    AccountAgeWitnessService,
)
from bisq.core.filter.filter_manager import FilterManager
from bisq.core.offer.offer_filter_service_result import OfferFilterServiceResult
from bisq.core.payment.payment_account import PaymentAccount
from bisq.core.payment.payment_account_util import PaymentAccountUtil
from bisq.core.user.preferences import Preferences
from bisq.core.user.user import User
from bisq.common.version import Version
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer

logger = get_logger(__name__)


class OfferFilterService:

    def __init__(
        self,
        user: "User",
        preferences: "Preferences",
        filter_manager: "FilterManager",
        account_age_witness_service: "AccountAgeWitnessService",
    ):
        self.user = user
        self.preferences = preferences
        self.filter_manager = filter_manager
        self.account_age_witness_service = account_age_witness_service

        # TODO: maybe replace with lru cache ?
        self.insufficient_counterparty_trade_limit_cache: dict[str, bool] = {}
        self.my_insufficient_trade_limit_cache: dict[str, bool] = {}

        if user:
            # If our accounts have changed we reset our myInsufficientTradeLimitCache as it depends on account data
            def on_accounts_changed(e):
                self.my_insufficient_trade_limit_cache.clear()

            user.payment_accounts_observable.add_listener(on_accounts_changed)

    def can_take_offer(
        self, offer: "Offer", is_taker_api_user: bool
    ) -> "OfferFilterServiceResult":
        if (
            is_taker_api_user
            and self.filter_manager.get_filter() is not None
            and self.filter_manager.get_filter().disable_api
        ):
            return OfferFilterServiceResult.API_DISABLED
        if not self.is_any_payment_account_valid_for_offer(offer):
            return OfferFilterServiceResult.HAS_NO_PAYMENT_ACCOUNT_VALID_FOR_OFFER
        if not self.has_same_protocol_version(offer):
            return OfferFilterServiceResult.HAS_NOT_SAME_PROTOCOL_VERSION
        if self.is_ignored(offer):
            return OfferFilterServiceResult.IS_IGNORED
        if self.is_offer_banned(offer):
            return OfferFilterServiceResult.IS_OFFER_BANNED
        if self.is_currency_banned(offer):
            return OfferFilterServiceResult.IS_CURRENCY_BANNED
        if self.is_payment_method_banned(offer):
            return OfferFilterServiceResult.IS_PAYMENT_METHOD_BANNED
        if self.is_node_address_banned(offer):
            return OfferFilterServiceResult.IS_NODE_ADDRESS_BANNED
        if self.require_update_to_new_version():
            return OfferFilterServiceResult.REQUIRE_UPDATE_TO_NEW_VERSION
        if self.is_insufficient_counterparty_trade_limit(offer):
            return OfferFilterServiceResult.IS_INSUFFICIENT_COUNTERPARTY_TRADE_LIMIT
        if self.is_my_insufficient_trade_limit(offer):
            return OfferFilterServiceResult.IS_MY_INSUFFICIENT_TRADE_LIMIT

        return OfferFilterServiceResult.VALID

    def is_any_payment_account_valid_for_offer(self, offer: "Offer") -> bool:
        return (
            self.user.payment_accounts is not None
            and PaymentAccountUtil.is_any_payment_account_valid_for_offer(
                offer,
                self.user.payment_accounts,
            )
        )

    def has_same_protocol_version(self, offer: "Offer") -> bool:
        return offer.protocol_version == Version.TRADE_PROTOCOL_VERSION

    def is_ignored(self, offer: "Offer") -> bool:
        full_address = offer.maker_node_address.get_full_address()
        return any(
            i == full_address for i in self.preferences.get_ignore_traders_list()
        )

    def is_offer_banned(self, offer: "Offer") -> bool:
        return self.filter_manager.is_offer_id_banned(offer.id)

    def is_currency_banned(self, offer: "Offer") -> bool:
        return self.filter_manager.is_currency_banned(offer.currency_code)

    def is_payment_method_banned(self, offer: "Offer") -> bool:
        return self.filter_manager.is_payment_method_banned(offer.payment_method)

    def is_node_address_banned(self, offer: "Offer") -> bool:
        return self.filter_manager.is_node_address_banned(offer.maker_node_address)

    def require_update_to_new_version(self) -> bool:
        return self.filter_manager.require_update_to_new_version_for_trading()

    # This call is a bit expensive so we cache results
    def is_insufficient_counterparty_trade_limit(self, offer: "Offer") -> bool:
        offer_id = offer.id
        if offer_id in self.insufficient_counterparty_trade_limit_cache:
            return self.insufficient_counterparty_trade_limit_cache[offer_id]

        result = (
            offer.is_fiat_offer
            and not self.account_age_witness_service.verify_peers_trade_amount(
                offer, offer.amount, lambda x: None
            )
        )
        self.insufficient_counterparty_trade_limit_cache[offer_id] = result
        return result

    # This call is a bit expensive so we cache results
    def is_my_insufficient_trade_limit(self, offer: "Offer") -> bool:
        offer_id = offer.id
        if offer_id in self.my_insufficient_trade_limit_cache:
            return self.my_insufficient_trade_limit_cache[offer_id]

        account = PaymentAccountUtil.get_most_mature_payment_account_for_offer(
            offer, self.user.payment_accounts, self.account_age_witness_service
        )

        if account is not None:
            my_trade_limit = self.account_age_witness_service.get_my_trade_limit(
                account, offer.currency_code, offer.mirrored_direction
            )
        else:
            my_trade_limit = 0

        offer_min_amount = offer.min_amount.value
        logger.debug(
            f"isInsufficientTradeLimit account={account.account_name if account else 'None'}, "
            f"myTradeLimit={Coin.value_of(my_trade_limit).to_friendly_string()}, "
            f"offerMinAmount={Coin.value_of(offer_min_amount).to_friendly_string()}"
        )
        result = account is not None and my_trade_limit < offer_min_amount
        self.my_insufficient_trade_limit_cache[offer_id] = result
        return result

    def reset_trade_limit_cache(self):
        self.my_insufficient_trade_limit_cache.clear()
