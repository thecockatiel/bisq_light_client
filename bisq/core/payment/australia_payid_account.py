from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.australia_payid_account_payload import (
    AustraliaPayidAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class AustraliaPayidAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("AUD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.AUSTRALIA_PAYID)
        self.set_single_trade_currency(AustraliaPayidAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return AustraliaPayidAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return AustraliaPayidAccount.SUPPORTED_CURRENCIES

    @property
    def payid(self):
        return self._australia_payid_account_payload.payid

    @payid.setter
    def payid(self, value: str):
        if value is None:
            value = ""
        self._australia_payid_account_payload.payid = value

    @property
    def bank_account_name(self):
        return self._australia_payid_account_payload.bank_account_name

    @bank_account_name.setter
    def bank_account_name(self, value: str):
        if value is None:
            value = ""
        self._australia_payid_account_payload.bank_account_name = value

    @property
    def _australia_payid_account_payload(self):
        assert isinstance(self.payment_account_payload, AustraliaPayidAccountPayload)
        return self.payment_account_payload
