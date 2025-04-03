from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.paxum_account_payload import (
    PaxumAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class PaxumAccount(PaymentAccount):

    # https://github.com/bisq-network/growth/issues/235
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
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

    def create_payload(self) -> PaymentAccountPayload:
        return PaxumAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return PaxumAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._paxum_account_payload.email

    @email.setter
    def email(self, value: str):
        if value is None:
            value = ""
        self._paxum_account_payload.email = value

    @property
    def _paxum_account_payload(self):
        assert isinstance(self.payment_account_payload, PaxumAccountPayload)
        return self.payment_account_payload
