from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.monese_account_payload import MoneseAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class MoneseAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = [
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("RON"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.MONESE)

    def create_payload(self):
        return MoneseAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return MoneseAccount.SUPPORTED_CURRENCIES

    @property
    def holder_name(self):
        return cast(MoneseAccountPayload, self.payment_account_payload).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(MoneseAccountPayload, self.payment_account_payload).holder_name = (
            value or ""
        )

    @property
    def mobile_nr(self):
        return cast(MoneseAccountPayload, self.payment_account_payload).mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        cast(MoneseAccountPayload, self.payment_account_payload).mobile_nr = value or ""

    def get_message_for_buyer(self):
        return "payment.monese.info.buyer"

    def get_message_for_seller(self):
        return "payment.monese.info.seller"

    def get_message_for_account_creation(self):
        return "payment.monese.info.account"
