from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.paxum_account_payload import (
    PaxumAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class PaxumAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AUD"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CZK"),
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("HUF"),
        FiatCurrency("IDR"),
        FiatCurrency("INR"),
        FiatCurrency("NOK"),
        FiatCurrency("NZD"),
        FiatCurrency("PLN"),
        FiatCurrency("RON"),
        FiatCurrency("SEK"),
        FiatCurrency("THB"),
        FiatCurrency("USD"),
        FiatCurrency("ZAR"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.PAXUM)
        self.trade_currencies.extend(PaxumAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return PaxumAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return PaxumAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(PaxumAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(PaxumAccountPayload, self.payment_account_payload).email = value or ""
