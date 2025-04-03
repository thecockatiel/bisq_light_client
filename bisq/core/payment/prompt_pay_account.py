from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.prompt_pay_account_payload import (
    PromptPayAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class PromptPayAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("THB"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.PROMPT_PAY)
        self.set_single_trade_currency(PromptPayAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return PromptPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return PromptPayAccount.SUPPORTED_CURRENCIES

    @property
    def prompt_pay_id(self):
        return self._prompt_pay_account_payload.prompt_pay_id

    @prompt_pay_id.setter
    def prompt_pay_id(self, value: str):
        if value is None:
            value = ""
        self._prompt_pay_account_payload.prompt_pay_id = value

    @property
    def _prompt_pay_account_payload(self):
        assert isinstance(self.payment_account_payload, PromptPayAccountPayload)
        return self.payment_account_payload
