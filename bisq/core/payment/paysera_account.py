from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.paysera_account_payload import (
    PayseraAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class PayseraAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AUD"),
        FiatCurrency("BGN"),
        FiatCurrency("BYN"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CNY"),
        FiatCurrency("CZK"),
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("GEL"),
        FiatCurrency("HKD"),
        FiatCurrency("HRK"),
        FiatCurrency("HUF"),
        FiatCurrency("ILS"),
        FiatCurrency("INR"),
        FiatCurrency("JPY"),
        FiatCurrency("KZT"),
        FiatCurrency("MXN"),
        FiatCurrency("NOK"),
        FiatCurrency("NZD"),
        FiatCurrency("PHP"),
        FiatCurrency("PLN"),
        FiatCurrency("RON"),
        FiatCurrency("RSD"),
        FiatCurrency("RUB"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("THB"),
        FiatCurrency("TRY"),
        FiatCurrency("USD"),
        FiatCurrency("ZAR")
    ]

    def __init__(self):
        super().__init__(PaymentMethod.PAYSERA)
        self.trade_currencies.extend(PayseraAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return PayseraAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return PayseraAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(PayseraAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(PayseraAccountPayload, self.payment_account_payload).email = (
            value or ""
        )
