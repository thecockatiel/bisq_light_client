from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.nequi_account_payload import NequiAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class NequiAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("COP")]

    def __init__(self):
        super().__init__(PaymentMethod.NEQUI)

    def create_payload(self):
        return NequiAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return NequiAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self):
        return cast(NequiAccountPayload, self.payment_account_payload).mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        cast(NequiAccountPayload, self.payment_account_payload).mobile_nr = value or ""

    def get_message_for_buyer(self):
        return "payment.nequi.info.buyer"

    def get_message_for_seller(self):
        return "payment.nequi.info.seller"

    def get_message_for_account_creation(self):
        return "payment.nequi.info.account"
