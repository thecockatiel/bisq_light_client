from typing import cast
from bisq.core.locale.currency_util import CurrencyUtil
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.national_bank_account_payload import (
    NationalBankAccountPayload,
)
from bisq.core.payment.payload.bank_account_payload import BankAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)


class NationalBankAccount(CountryBasedPaymentAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES = CurrencyUtil.get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.NATIONAL_BANK)

    def create_payload(self):
        return NationalBankAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return NationalBankAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return cast(BankAccountPayload, self.payment_account_payload).bank_id

    @property
    def country_code(self):
        return self.country.code if self.country else ""
