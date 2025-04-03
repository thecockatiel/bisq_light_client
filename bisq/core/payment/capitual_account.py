from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.capitual_account_payload import (
    CapitualAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class CapitualAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("BRL"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.CAPITUAL)
        self.trade_currencies.extend(CapitualAccount.SUPPORTED_CURRENCIES)

    def create_payload(self) -> PaymentAccountPayload:
        return CapitualAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return CapitualAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return self._capitual_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        self._capitual_account_payload.account_nr = value

    @property
    def _capitual_account_payload(self):
        assert isinstance(self.payment_account_payload, CapitualAccountPayload)
        return self.payment_account_payload
