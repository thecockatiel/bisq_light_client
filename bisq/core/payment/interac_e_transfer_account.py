from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.interac_e_transfer_account_payload import (
    InteracETransferAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class InteracETransferAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("CAD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.INTERAC_E_TRANSFER)
        self.set_single_trade_currency(InteracETransferAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return InteracETransferAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return InteracETransferAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._interac_e_transfer_account_payload.email

    @email.setter
    def email(self, value: str):
        if value is None:
            value = ""
        self._interac_e_transfer_account_payload.email = value

    @property
    def answer(self):
        return self._interac_e_transfer_account_payload.answer

    @answer.setter
    def answer(self, value: str):
        if value is None:
            value = ""
        self._interac_e_transfer_account_payload.answer = value

    @property
    def question(self):
        return self._interac_e_transfer_account_payload.question

    @question.setter
    def question(self, value: str):
        if value is None:
            value = ""
        self._interac_e_transfer_account_payload.question = value

    @property
    def holder_name(self):
        return self._interac_e_transfer_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        if value is None:
            value = ""
        self._interac_e_transfer_account_payload.holder_name = value

    @property
    def _interac_e_transfer_account_payload(self):
        assert isinstance(self.payment_account_payload, InteracETransferAccountPayload)
        return self.payment_account_payload
