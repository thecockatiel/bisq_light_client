from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.bizum_account_payload import BizumAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class BizumAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("EUR")]

    def __init__(self):
        super().__init__(PaymentMethod.BIZUM)

    def create_payload(self):
        return BizumAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return BizumAccount.SUPPORTED_CURRENCIES

    @property
    def mobile_nr(self):
        return cast(BizumAccountPayload, self.payment_account_payload).mobile_nr

    @mobile_nr.setter
    def mobile_nr(self, value: str):
        cast(BizumAccountPayload, self.payment_account_payload).mobile_nr = value or ""

    def get_message_for_buyer(self):
        return "payment.bizum.info.buyer"

    def get_message_for_seller(self):
        return "payment.bizum.info.seller"

    def get_message_for_account_creation(self):
        return "payment.bizum.info.account"
