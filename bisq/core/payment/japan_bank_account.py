from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.japan_bank_account_payload import (
    JapanBankAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class JapanBankAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("JPY"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.JAPAN_BANK)
        self.set_single_trade_currency(JapanBankAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return JapanBankAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return JapanBankAccount.SUPPORTED_CURRENCIES

    @property
    def bank_code(self):
        return self._japan_bank_account_payload.bank_code

    @bank_code.setter
    def bank_code(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_code = value

    @property
    def bank_name(self):
        return self._japan_bank_account_payload.bank_name

    @bank_name.setter
    def bank_name(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_name = value

    @property
    def bank_branch_code(self):
        return self._japan_bank_account_payload.bank_branch_code

    @bank_branch_code.setter
    def bank_branch_code(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_branch_code = value

    @property
    def bank_branch_name(self):
        return self._japan_bank_account_payload.bank_branch_name

    @bank_branch_name.setter
    def bank_branch_name(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_branch_name = value

    @property
    def bank_account_type(self):
        return self._japan_bank_account_payload.bank_account_type

    @bank_account_type.setter
    def bank_account_type(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_account_type = value

    @property
    def bank_account_number(self):
        return self._japan_bank_account_payload.bank_account_number

    @bank_account_number.setter
    def bank_account_number(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_account_number = value

    @property
    def bank_account_name(self):
        return self._japan_bank_account_payload.bank_account_name

    @bank_account_name.setter
    def bank_account_name(self, value: str):
        if value is None:
            value = ""
        self._japan_bank_account_payload.bank_account_name = value

    @property
    def _japan_bank_account_payload(self):
        assert isinstance(self.payment_account_payload, JapanBankAccountPayload)
        return self.payment_account_payload
