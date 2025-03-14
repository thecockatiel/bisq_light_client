from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.prompt_pay_account_payload import PromptPayAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class PromptPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("THB")]

    def __init__(self):
        super().__init__(PaymentMethod.PROMPT_PAY)
        self.set_single_trade_currency(PromptPayAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return PromptPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return PromptPayAccount.SUPPORTED_CURRENCIES

    @property
    def prompt_pay_id(self):
        return cast(PromptPayAccountPayload, self.payment_account_payload).prompt_pay_id

    @prompt_pay_id.setter
    def prompt_pay_id(self, value: str):
        cast(PromptPayAccountPayload, self.payment_account_payload).prompt_pay_id = (
            value or ""
        )
