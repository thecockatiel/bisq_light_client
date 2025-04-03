from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.advanced_cash_account_payload import (
    AdvancedCashAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class AdvancedCashAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("BRL"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("KZT"),
        FiatCurrency("RUB"),
        FiatCurrency("UAH"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.PROMPT_PAY)
        self.trade_currencies.extend(AdvancedCashAccount.SUPPORTED_CURRENCIES)

    def create_payload(self) -> PaymentAccountPayload:
        return AdvancedCashAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return AdvancedCashAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return self._advanced_cash_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        if value is None:
            value = ""
        self._advanced_cash_account_payload.account_nr = value

    @property
    def _advanced_cash_account_payload(self):
        assert isinstance(self.payment_account_payload, AdvancedCashAccountPayload)
        return self.payment_account_payload
