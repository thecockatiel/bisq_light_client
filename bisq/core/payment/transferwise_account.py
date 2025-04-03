from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.transferwise_account_payload import (
    TransferwiseAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class TransferwiseAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
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

    def create_payload(self) -> PaymentAccountPayload:
        return TransferwiseAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return TransferwiseAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._transferwise_account_payload.email

    @email.setter
    def email(self, value: str):
        if value is None:
            value = ""
        self._transferwise_account_payload.email = value

    @property
    def _transferwise_account_payload(self):
        assert isinstance(self.payment_account_payload, TransferwiseAccountPayload)
        return self.payment_account_payload
