from typing import TYPE_CHECKING, List, cast
from bisq.core.locale.currency_util import get_all_fiat_currencies
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.national_bank_account_payload import (
    NationalBankAccountPayload,
)
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class NationalBankAccount(CountryBasedPaymentAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.NATIONAL_BANK)

    def create_payload(self) -> "PaymentAccountPayload":
        return NationalBankAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> List["TradeCurrency"]:
        return NationalBankAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return self._national_bank_account_payload.bank_id

    @property
    def country_code(self):
        country = super().country
        return country.code if country else ""

    @property
    def _national_bank_account_payload(self):
        assert isinstance(self.payment_account_payload, NationalBankAccountPayload)
        return self.payment_account_payload
