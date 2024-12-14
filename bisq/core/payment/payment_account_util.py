from typing import TYPE_CHECKING, List, Optional
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.specific_banks_account import SpecificBanksAccount
from bisq.core.payment.same_bank_account import SameBankAccount
from bisq.core.payment.sepa_account import SepaAccount
from bisq.core.payment.sepa_instant_account import SepaInstantAccount
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.bank_account import BankAccount
from bisq.core.payment.amazon_gift_card_account import AmazonGiftCardAccount

if TYPE_CHECKING:
    from bisq.core.user.user import User
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.locale.country import Country
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload

# TODO: implement rest of the class
class PaymentAccountUtil:

    @staticmethod
    def get_accepted_country_codes(payment_account: "PaymentAccount") -> Optional[List[str]]:
        accepted_country_codes = None
        if isinstance(payment_account, SepaAccount):
            accepted_country_codes = list(payment_account.accepted_country_codes)
        elif isinstance(payment_account, SepaInstantAccount):
            accepted_country_codes = list(payment_account.accepted_country_codes)
        elif isinstance(payment_account, CountryBasedPaymentAccount):
            accepted_country_codes = []
            country = payment_account.country
            if country is not None:
                accepted_country_codes.append(country.code)
        return accepted_country_codes
    
    @staticmethod
    def get_accepted_banks(payment_account: "PaymentAccount") -> Optional[List[str]]:
        accepted_banks = None
        if isinstance(payment_account, SpecificBanksAccount):
            accepted_banks = list(payment_account.accepted_banks)
        elif isinstance(payment_account, SameBankAccount):
            accepted_banks = [payment_account.bank_id]
        return accepted_banks

    @staticmethod
    def get_bank_id(payment_account: "PaymentAccount") -> Optional[str]:
        return payment_account.bank_id if isinstance(payment_account, BankAccount) else None

    @staticmethod
    def get_country_code(payment_account: "PaymentAccount") -> Optional[str]:
        if isinstance(payment_account, CountryBasedPaymentAccount):
            country = payment_account.country
            return country.code if country is not None else None
        elif isinstance(payment_account, AmazonGiftCardAccount):
            country = payment_account.country
            return country.code if country is not None else None
        return None

    @staticmethod
    def is_cryptocurrency_account(payment_account: "PaymentAccount"):
        return payment_account is not None and payment_account.payment_method in [
            PaymentMethod.BLOCK_CHAINS,
            PaymentMethod.BLOCK_CHAINS_INSTANT,
        ]

    @staticmethod
    def find_payment_account(payment_account_payload: "PaymentAccountPayload", user: "User") -> Optional["PaymentAccount"]:
        for account in user.payment_accounts_observable:
            if account.payment_account_payload == payment_account_payload:
                return account
        return None
