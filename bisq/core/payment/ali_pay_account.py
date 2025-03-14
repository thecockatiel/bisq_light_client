from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.ali_pay_account_payload import (
    AliPayAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class AliPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("CNY")]

    def __init__(self):
        super().__init__(PaymentMethod.ALI_PAY)
        self.set_single_trade_currency(AliPayAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return AliPayAccountPayload(self.payment_method.id, self.id)

    @property
    def _ali_pay_account_payload(self):
        return cast(AliPayAccountPayload, self.payment_account_payload)

    def get_supported_currencies(self):
        return AliPayAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return self._ali_pay_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        self._ali_pay_account_payload.account_nr = value
