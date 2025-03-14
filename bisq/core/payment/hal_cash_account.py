from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.hal_cash_account_payload import (
    HalCashAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class HalCashAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.HAL_CASH)
        self.set_single_trade_currency(HalCashAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return HalCashAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return HalCashAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self):
        return cast(HalCashAccountPayload, self.payment_account_payload).mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        cast(HalCashAccountPayload, self.payment_account_payload).mobile_nr = (
            value or ""
        )
