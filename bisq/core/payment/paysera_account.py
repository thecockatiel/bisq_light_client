from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.paysera_account_payload import (
    PayseraAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class PayseraAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
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
        FiatCurrency("ZAR"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.PAYSERA)

    def create_payload(self) -> PaymentAccountPayload:
        return PayseraAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return PayseraAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._paysera_account_payload.email

    @email.setter
    def email(self, value: str):
        if value is None:
            value = ""
        self._paysera_account_payload.email = value

    @property
    def _paysera_account_payload(self):
        assert isinstance(self.payment_account_payload, PayseraAccountPayload)
        return self.payment_account_payload
