from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.interac_e_transfer_account_payload import (
    InteracETransferAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class InteracETransferAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("CAD")]

    def __init__(self):
        super().__init__(PaymentMethod.INTERAC_E_TRANSFER)
        self.set_single_trade_currency(InteracETransferAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return InteracETransferAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return InteracETransferAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(InteracETransferAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(InteracETransferAccountPayload, self.payment_account_payload).email = (
            value or ""
        )

    @property
    def answer(self):
        return cast(InteracETransferAccountPayload, self.payment_account_payload).answer

    @answer.setter
    def answer(self, value: str):
        cast(InteracETransferAccountPayload, self.payment_account_payload).answer = (
            value or ""
        )

    @property
    def question(self):
        return cast(
            InteracETransferAccountPayload, self.payment_account_payload
        ).question

    @question.setter
    def question(self, value: str):
        cast(InteracETransferAccountPayload, self.payment_account_payload).question = (
            value or ""
        )

    @property
    def holder_name(self):
        return cast(
            InteracETransferAccountPayload, self.payment_account_payload
        ).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(
            InteracETransferAccountPayload, self.payment_account_payload
        ).holder_name = (value or "")
