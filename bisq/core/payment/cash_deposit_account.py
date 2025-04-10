from typing import TYPE_CHECKING, List, cast
from bisq.core.locale.currency_util import get_all_sorted_fiat_currencies
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.cash_deposit_account_payload import (
    CashDepositAccountPayload,
)
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class CashDepositAccount(CountryBasedPaymentAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = get_all_sorted_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.CASH_DEPOSIT)

    def create_payload(self) -> "PaymentAccountPayload":
        return CashDepositAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> List["TradeCurrency"]:
        return CashDepositAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return self._cash_deposit_account_payload.bank_id

    @property
    def country_code(self):
        country = super().country
        return country.code if country else ""

    @property
    def requirements(self):
        return self._cash_deposit_account_payload.requirements

    @property
    def _cash_deposit_account_payload(self):
        assert isinstance(self.payment_account_payload, CashDepositAccountPayload)
        return self.payment_account_payload
