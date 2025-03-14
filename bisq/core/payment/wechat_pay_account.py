from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.we_chat_pay_account_payload import (
    WeChatPayAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class WeChatPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("CNY")]

    def __init__(self):
        super().__init__(PaymentMethod.WECHAT_PAY)
        self.set_single_trade_currency(WeChatPayAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return WeChatPayAccountPayload(self.payment_method.id, self.id)

    @property
    def _we_chat_pay_account_payload(self):
        return cast(WeChatPayAccountPayload, self.payment_account_payload)

    def get_supported_currencies(self):
        return WeChatPayAccount.SUPPORTED_CURRENCIES

    @property
    def account_nr(self):
        return self._we_chat_pay_account_payload.account_nr

    @account_nr.setter
    def account_nr(self, value: str):
        self._we_chat_pay_account_payload.account_nr = value
