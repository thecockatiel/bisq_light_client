from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.swish_account_payload import (
    SwishAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class SwishAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("SEK")]

    def __init__(self):
        super().__init__(PaymentMethod.SWISH)
        self.set_single_trade_currency(SwishAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return SwishAccountPayload(self.payment_method.id, self.id)

    @property
    def _swish_pay_account_payload(self):
        return cast(SwishAccountPayload, self.payment_account_payload)

    def get_supported_currencies(self):
        return SwishAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self):
        return self._swish_pay_account_payload.mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        self._swish_pay_account_payload.mobile_nr = value

    @property
    def holder_name(self):
        return self._swish_pay_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._swish_pay_account_payload.holder_name = value
