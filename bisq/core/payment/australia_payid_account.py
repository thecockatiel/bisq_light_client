from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.australia_payid_account_payload import (
    AustraliaPayidAccountPayload,
)
from bisq.core.payment.payment_account import PaymentAccount


class AustraliaPayidAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("AUD")]

    def __init__(self):
        super().__init__(PaymentMethod.AUSTRALIA_PAYID)
        self.set_single_trade_currency(AustraliaPayidAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return AustraliaPayidAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return AustraliaPayidAccount.SUPPORTED_CURRENCIES

    @property
    def payid(self):
        return cast(AustraliaPayidAccountPayload, self.payment_account_payload).payid

    @payid.setter
    def payid(self, value: str):
        cast(AustraliaPayidAccountPayload, self.payment_account_payload).payid = (
            value or ""
        )

    @property
    def bank_account_name(self):
        return cast(
            AustraliaPayidAccountPayload, self.payment_account_payload
        ).bank_account_name

    @bank_account_name.setter
    def bank_account_name(self, value: str):
        cast(
            AustraliaPayidAccountPayload, self.payment_account_payload
        ).bank_account_name = (value or "")
