from typing import TYPE_CHECKING

from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount


if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.payment.receipt_predicates import ReceiptPredicates


class ReceiptValidator:
    def __init__(
        self,
        offer: "Offer",
        account: "PaymentAccount",
        predicates: "ReceiptPredicates" = None,
    ):
        if predicates is None:
            from bisq.core.payment.receipt_predicates import ReceiptPredicates
            predicates = ReceiptPredicates()

        self.offer = offer
        self.account = account
        self.predicates = predicates

    def is_valid(self) -> bool:
        # We only support trades with the same currencies
        if not self.predicates.is_matching_currency(self.offer, self.account):
            return False

        is_equal_payment_methods = self.predicates.is_equal_payment_methods(
            self.offer, self.account
        )

        # All non-CountryBasedPaymentAccount need to have same payment methods
        if not isinstance(self.account, CountryBasedPaymentAccount):
            return is_equal_payment_methods

        # We have a CountryBasedPaymentAccount, countries need to match
        if not self.predicates.is_matching_country_codes(self.offer, self.account):
            return False

        # We have same country
        if self.predicates.is_matching_sepa_offer(self.offer, self.account):
            # Sepa offer and taker account is Sepa or Sepa Instant
            return True

        if self.predicates.is_matching_sepa_instant(self.offer, self.account):
            # Sepa Instant offer and taker account
            return True

        # Aside from Sepa or Sepa Instant, payment methods need to match
        if not is_equal_payment_methods:
            return False

        if self.predicates.is_offer_require_same_or_specific_bank(
            self.offer, self.account
        ):
            return self.predicates.is_matching_bank_id(self.offer, self.account)

        return True
