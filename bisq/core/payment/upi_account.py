from typing import cast
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.upi_account_payload import UpiAccountPayload
from bisq.core.payment.payment_account import IfscBasedAccount


class UpiAccount(IfscBasedAccount):
    def __init__(self):
        super().__init__(PaymentMethod.UPI)

    def create_payload(self):
        return UpiAccountPayload(self.payment_method.id, self.id)

    @property
    def virtual_payment_address(self):
        return cast(UpiAccountPayload, self.payment_account_payload).virtual_payment_address

    @virtual_payment_address.setter
    def virtual_payment_address(self, value: str):
        cast(UpiAccountPayload, self.payment_account_payload).virtual_payment_address = value or ""

    def get_message_for_buyer(self):
        return "payment.upi.info.buyer"

    def get_message_for_seller(self):
        return "payment.upi.info.seller"

    def get_message_for_account_creation(self):
        return "payment.upi.info.account"
