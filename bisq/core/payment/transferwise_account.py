from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.transferwise_account_payload import (
    TransferwiseAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class TransferwiseAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AED"),
        FiatCurrency("ARS"),
        FiatCurrency("AUD"),
        FiatCurrency("BDT"),
        FiatCurrency("BGN"),
        FiatCurrency("BRL"),
        FiatCurrency("BWP"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CLP"),
        FiatCurrency("CNY"),
        FiatCurrency("COP"),
        FiatCurrency("CRC"),
        FiatCurrency("CZK"),
        FiatCurrency("DKK"),
        FiatCurrency("EGP"),
        FiatCurrency("EUR"),
        FiatCurrency("FJD"),
        FiatCurrency("GBP"),
        FiatCurrency("GEL"),
        FiatCurrency("GHS"),
        FiatCurrency("HKD"),
        FiatCurrency("HRK"),
        FiatCurrency("HUF"),
        FiatCurrency("IDR"),
        FiatCurrency("ILS"),
        FiatCurrency("INR"),
        FiatCurrency("JPY"),
        FiatCurrency("KES"),
        FiatCurrency("KRW"),
        FiatCurrency("LKR"),
        FiatCurrency("MAD"),
        FiatCurrency("MXN"),
        FiatCurrency("MYR"),
        FiatCurrency("NOK"),
        FiatCurrency("NPR"),
        FiatCurrency("NZD"),
        FiatCurrency("PEN"),
        FiatCurrency("PHP"),
        FiatCurrency("PKR"),
        FiatCurrency("PLN"),
        FiatCurrency("RON"),
        FiatCurrency("RUB"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("THB"),
        FiatCurrency("TRY"),
        FiatCurrency("UAH"),
        FiatCurrency("UGX"),
        FiatCurrency("UYU"),
        FiatCurrency("VND"),
        FiatCurrency("XOF"),
        FiatCurrency("ZAR"),
        FiatCurrency("ZMW"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.TRANSFERWISE)
        self.trade_currencies.extend(TransferwiseAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return TransferwiseAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return TransferwiseAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(TransferwiseAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(TransferwiseAccountPayload, self.payment_account_payload).email = (
            value or ""
        )
