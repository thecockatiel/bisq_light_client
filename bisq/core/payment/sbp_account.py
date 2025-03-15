from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.sbp_account_payload import SbpAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class SbpAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("RUB")]

    def __init__(self):
        super().__init__(PaymentMethod.SBP)
        self.set_single_trade_currency(SbpAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return SbpAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return SbpAccount.SUPPORTED_CURRENCIES

    def get_message_for_account_creation(self):
        return "payment.sbp.info.account"

    @property
    def mobile_number(self):
        return cast(SbpAccountPayload, self.payment_account_payload).mobile_number

    @mobile_number.setter
    def mobile_number(self, value: str):
        cast(SbpAccountPayload, self.payment_account_payload).mobile_number = (
            value or ""
        )

    @property
    def bank_name(self):
        return cast(SbpAccountPayload, self.payment_account_payload).bank_name

    @bank_name.setter
    def bank_name(self, value: str):
        cast(SbpAccountPayload, self.payment_account_payload).bank_name = value or ""
