from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.japan_bank_account_payload import JapanBankAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class JapanBankAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("JPY")]

    def __init__(self):
        super().__init__(PaymentMethod.JAPAN_BANK)
        self.set_single_trade_currency(JapanBankAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return JapanBankAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return JapanBankAccount.SUPPORTED_CURRENCIES

    @property
    def bank_code(self):
        return cast(JapanBankAccountPayload, self.payment_account_payload).bank_code

    @bank_code.setter
    def bank_code(self, value: str):
        cast(JapanBankAccountPayload, self.payment_account_payload).bank_code = (
            value or ""
        )

    @property
    def bank_name(self):
        return cast(JapanBankAccountPayload, self.payment_account_payload).bank_name

    @bank_name.setter
    def bank_name(self, value: str):
        cast(JapanBankAccountPayload, self.payment_account_payload).bank_name = (
            value or ""
        )

    @property
    def bank_branch_code(self):
        return cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_branch_code

    @bank_branch_code.setter
    def bank_branch_code(self, value: str):
        cast(JapanBankAccountPayload, self.payment_account_payload).bank_branch_code = (
            value or ""
        )

    @property
    def bank_branch_name(self):
        return cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_branch_name

    @bank_branch_name.setter
    def bank_branch_name(self, value: str):
        cast(JapanBankAccountPayload, self.payment_account_payload).bank_branch_name = (
            value or ""
        )

    @property
    def bank_account_type(self):
        return cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_account_type

    @bank_account_type.setter
    def bank_account_type(self, value: str):
        cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_account_type = (value or "")

    @property
    def bank_account_number(self):
        return cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_account_number

    @bank_account_number.setter
    def bank_account_number(self, value: str):
        cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_account_number = (value or "")

    @property
    def bank_account_name(self):
        return cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_account_name

    @bank_account_name.setter
    def bank_account_name(self, value: str):
        cast(
            JapanBankAccountPayload, self.payment_account_payload
        ).bank_account_name = (value or "")
