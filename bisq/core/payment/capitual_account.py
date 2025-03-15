from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.capitual_account_payload import CapitualAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class CapitualAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("BRL"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.CAPITUAL)
        self.trade_currencies.extend(CapitualAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return CapitualAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return CapitualAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return cast(CapitualAccountPayload, self.payment_account_payload).account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        cast(CapitualAccountPayload, self.payment_account_payload).account_nr = (
            value or ""
        )
