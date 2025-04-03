from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.uphold_account_payload import (
    UpholdAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


# JAVA TODO missing support for selected trade currency
class UpholdAccount(PaymentAccount):

    # https://support.uphold.com/hc/en-us/articles/202473803-Supported-currencies
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
        super().__init__(PaymentMethod.UPHOLD)
        self.trade_currencies.extend(
            UpholdAccount.SUPPORTED_CURRENCIES,
        )

    def create_payload(self) -> PaymentAccountPayload:
        return UpholdAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return UpholdAccount.SUPPORTED_CURRENCIES

    @property
    def account_id(self):
        return self._uphold_account_payload.account_id

    @account_id.setter
    def account_id(self, value):
        self._uphold_account_payload.account_id = value

    @property
    def account_owner(self):
        return self._uphold_account_payload.account_owner
    
    @account_owner.setter
    def account_owner(self, value):
        if value is None:
            value = ""
        self._uphold_account_payload.account_owner = value

    @property
    def _uphold_account_payload(self):
        assert isinstance(self.payment_account_payload, UpholdAccountPayload)
        return self.payment_account_payload
