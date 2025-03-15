from typing import cast
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.paytm_account_payload import PaytmAccountPayload
from bisq.core.payment.payment_account import IfscBasedAccount


class PaytmAccount(IfscBasedAccount):
    def __init__(self):
        super().__init__(PaymentMethod.PAYTM)

    def create_payload(self):
        return PaytmAccountPayload(self.payment_method.id, self.id)

    @property
    def email_or_mobile_nr(self):
        return cast(PaytmAccountPayload, self.payment_account_payload).email_or_mobile_nr

    @email_or_mobile_nr.setter
    def email_or_mobile_nr(self, value: str):
        cast(PaytmAccountPayload, self.payment_account_payload).email_or_mobile_nr = value or ""

    def get_message_for_buyer(self):
        return "payment.paytm.info.buyer"

    def get_message_for_seller(self):
        return "payment.paytm.info.seller"

    def get_message_for_account_creation(self):
        return "payment.paytm.info.account"
