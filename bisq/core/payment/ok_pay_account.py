from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.ok_pay_account_payload import OKPayAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class OKPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AED"),
        FiatCurrency("ARS"),
        FiatCurrency("AUD"),
        FiatCurrency("BRL"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CNY"),
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("HKD"),
        FiatCurrency("ILS"),
        FiatCurrency("INR"),
        FiatCurrency("JPY"),
        FiatCurrency("KES"),
        FiatCurrency("MXN"),
        FiatCurrency("NOK"),
        FiatCurrency("NZD"),
        FiatCurrency("PHP"),
        FiatCurrency("PLN"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.OK_PAY)
        self.trade_currencies.extend(OKPayAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return OKPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return OKPayAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return cast(OKPayAccountPayload, self.payment_account_payload).account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        cast(OKPayAccountPayload, self.payment_account_payload).account_nr = value or ""
