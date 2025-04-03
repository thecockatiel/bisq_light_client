from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.ok_pay_account_payload import (
    OKPayAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


# Cannot be deleted as it would break old trade history entries
# Deprecated
class OKPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
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

    def create_payload(self) -> PaymentAccountPayload:
        return OKPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return OKPayAccount.SUPPORTED_CURRENCIES

    @property
    def _ok_pay_account_payload(self):
        assert isinstance(self.payment_account_payload, OKPayAccountPayload)
        return self.payment_account_payload

    @property
    def account_nr(self) -> str:
        return self._ok_pay_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str) -> None:
        self._ok_pay_account_payload.account_nr = value
