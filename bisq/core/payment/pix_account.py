from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.pix_account_payload import PixAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class PixAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("BRL")]

    def __init__(self):
        super().__init__(PaymentMethod.PIX)

    def create_payload(self):
        return PixAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return PixAccount.SUPPORTED_CURRENCIES

    @property
    def pix_key(self):
        return cast(PixAccountPayload, self.payment_account_payload).pix_key

    @pix_key.setter
    def pix_key(self, value: str):
        cast(PixAccountPayload, self.payment_account_payload).pix_key = value or ""

    def get_message_for_buyer(self):
        return "payment.pix.info.buyer"

    def get_message_for_seller(self):
        return "payment.pix.info.seller"

    def get_message_for_account_creation(self):
        return "payment.pix.info.account"
