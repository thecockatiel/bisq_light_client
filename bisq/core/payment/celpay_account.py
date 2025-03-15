from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.cel_pay_account_payload import CelPayAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class CelPayAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AUD"),
        FiatCurrency("CAD"),
        FiatCurrency("GBP"),
        FiatCurrency("HKD"),
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.CELPAY)

    def create_payload(self):
        return CelPayAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return CelPayAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(CelPayAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(CelPayAccountPayload, self.payment_account_payload).email = value or ""

    def get_message_for_buyer(self):
        return "payment.celpay.info.buyer"

    def get_message_for_seller(self):
        return "payment.celpay.info.seller"

    def get_message_for_account_creation(self):
        return "payment.celpay.info.account"
