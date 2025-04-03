from typing import cast
from bisq.core.locale.currency_util import get_all_fiat_currencies
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.bank_name_restricted_bank_account import (
    BankNameRestrictedBankAccount,
)
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.same_bank_account_payload import SameBankAccountPayload
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)


class SameBankAccount(
    CountryBasedPaymentAccount,
    BankNameRestrictedBankAccount,
    SameCountryRestrictedBankAccount,
):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.SAME_BANK)

    def create_payload(self):
        return SameBankAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return SameBankAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return self._same_bank_account_payload.bank_id

    @property
    def country_code(self):
        return self.country.code if self.country else ""

    @property
    def _same_bank_account_payload(self):
        assert isinstance(self.payment_account_payload, SameBankAccountPayload)
        return self.payment_account_payload
