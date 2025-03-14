from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.advanced_cash_account_payload import (
    AdvancedCashAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class AdvancedCashAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("BRL"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("KZT"),
        FiatCurrency("RUB"),
        FiatCurrency("UAH"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.ADVANCED_CASH)
        self.trade_currencies.extend(AdvancedCashAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return AdvancedCashAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return AdvancedCashAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return cast(AdvancedCashAccountPayload, self.payment_account_payload).account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        cast(AdvancedCashAccountPayload, self.payment_account_payload).account_nr = (
            value or ""
        )
