from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.chase_quick_pay_account_payload import (
    ChaseQuickPayAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class ChaseQuickPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.CHASE_QUICK_PAY)
        self.set_single_trade_currency(ChaseQuickPayAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return ChaseQuickPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return ChaseQuickPayAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(ChaseQuickPayAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(ChaseQuickPayAccountPayload, self.payment_account_payload).email = (
            value or ""
        )

    @property
    def holder_name(self):
        return cast(
            ChaseQuickPayAccountPayload, self.payment_account_payload
        ).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(ChaseQuickPayAccountPayload, self.payment_account_payload).holder_name = (
            value or ""
        )
