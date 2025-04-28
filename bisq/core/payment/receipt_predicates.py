import logging
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.core.payment.bank_account import BankAccount
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account_util import PaymentAccountUtil
from bisq.core.payment.sepa_account import SepaAccount
from bisq.core.payment.sepa_instant_account import SepaInstantAccount
from bisq.core.payment.specific_banks_account import SpecificBanksAccount

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.payment.payment_account import PaymentAccount



class ReceiptPredicates:
    def __init__(self):
        self.logger = get_ctx_logger(__name__)
        
    def is_equal_payment_methods(
        self, offer: "Offer", account: "PaymentAccount"
    ) -> bool:
        # check if we have a matching payment method or if its a bank account payment method which is treated special
        account_payment_method = account.payment_method
        offer_payment_method = offer.payment_method

        are_payment_methods_equal = account_payment_method == offer_payment_method

        if self.logger.isEnabledFor(logging.WARNING):
            account_payment_method_id = account_payment_method.id
            offer_payment_method_id = offer_payment_method.id
            if (
                not are_payment_methods_equal
                and account_payment_method_id == offer_payment_method_id
            ):
                self.logger.warning(
                    PaymentAccountUtil.get_info_for_mismatching_payment_method_limits(
                        offer, account
                    )
                )

        return are_payment_methods_equal

    def is_offer_require_same_or_specific_bank(
        self, offer: "Offer", account: "PaymentAccount"
    ) -> bool:
        payment_method = offer.payment_method
        is_same_or_specific_bank = (
            payment_method == PaymentMethod.SAME_BANK
            or payment_method == PaymentMethod.SPECIFIC_BANKS
        )
        return isinstance(account, BankAccount) and is_same_or_specific_bank

    def contains_case_insensitive(self, val: str, lst: list[str]) -> bool:
        return any(x.casefold() == val.casefold() for x in lst)

    def is_matching_bank_id(self, offer: "Offer", account: "PaymentAccount") -> bool:
        accepted_banks_for_offer = offer.accepted_bank_ids
        if accepted_banks_for_offer is None:
            raise ValueError("offer.accepted_bank_ids must not be None")

        if not isinstance(account, BankAccount):
            raise ValueError("account must be an instance of BankAccount")

        account_bank_id = account.bank_id

        if isinstance(account, SpecificBanksAccount):
            # check if we have a matching bank
            offer_side_matches_bank = (
                account_bank_id is not None
                and self.contains_case_insensitive(
                    account_bank_id, accepted_banks_for_offer
                )
            )
            accepted_banks_for_account = account.accepted_banks
            payment_account_side_matches_bank = self.contains_case_insensitive(
                offer.bank_id, accepted_banks_for_account
            )

            return offer_side_matches_bank and payment_account_side_matches_bank
        else:
            # national or same bank
            return account_bank_id is not None and self.contains_case_insensitive(
                account_bank_id, accepted_banks_for_offer
            )

    def is_matching_country_codes(
        self, offer: "Offer", account: "PaymentAccount"
    ) -> bool:
        accepted_codes = offer.accepted_country_codes or []

        try:
            code = (
                account.country.code
                if isinstance(account, CountryBasedPaymentAccount)
                else "undefined"
            )
        except AttributeError:
            code = "undefined"

        return code in accepted_codes

    def is_matching_currency(self, offer: "Offer", account: "PaymentAccount") -> bool:
        currencies = account.trade_currencies
        codes = {currency.code for currency in currencies}
        return offer.currency_code in codes

    def is_matching_sepa_offer(self, offer: "Offer", account: "PaymentAccount") -> bool:
        is_sepa = isinstance(account, SepaAccount)
        is_sepa_instant = isinstance(account, SepaInstantAccount)
        return offer.payment_method == PaymentMethod.SEPA and (
            is_sepa or is_sepa_instant
        )

    def is_matching_sepa_instant(
        self, offer: "Offer", account: "PaymentAccount"
    ) -> bool:
        return offer.payment_method == PaymentMethod.SEPA_INSTANT and isinstance(
            account, SepaInstantAccount
        )
