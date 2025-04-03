from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.swish_account_payload import (
    SwishAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class SwishAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("SEK"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.SWISH)
        self.set_single_trade_currency(SwishAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return SwishAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return SwishAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self):
        return self._swish_account_payload.mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        if value is None:
            value = ""
        self._swish_account_payload.mobile_nr = value

    @property
    def holder_name(self):
        return self._swish_account_payload.holder_name

    @mobile_nr.setter
    def holder_name(self, value: str):
        if value is None:
            value = ""
        self._swish_account_payload.holder_name = value

    @property
    def _swish_account_payload(self):
        assert isinstance(self.payment_account_payload, SwishAccountPayload)
        return self.payment_account_payload
