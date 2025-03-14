from typing import cast
from bisq.core.locale.currency_util import CurrencyUtil
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.cash_deposit_account_payload import (
    CashDepositAccountPayload,
)
from bisq.core.payment.payment_account import CountryBasedPaymentAccount
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)


class CashDepositAccount(CountryBasedPaymentAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES = CurrencyUtil.get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.CASH_DEPOSIT)

    def create_payload(self):
        return CashDepositAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return CashDepositAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return cast(CashDepositAccountPayload, self.payment_account_payload).bank_id

    @property
    def country_code(self):
        return self.country.code if self.country else ""

    @property
    def requirements(self):
        return cast(
            CashDepositAccountPayload, self.payment_account_payload
        ).requirements

    @requirements.setter
    def requirements(self, value: str):
        cast(CashDepositAccountPayload, self.payment_account_payload).requirements = (
            value or ""
        )
