from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.neft_account_payload import NeftAccountPayload
from bisq.core.payment.payment_account import IfscBasedAccount


class NeftAccount(IfscBasedAccount):
    def __init__(self):
        super().__init__(PaymentMethod.NEFT)

    def create_payload(self):
        return NeftAccountPayload(self.payment_method.id, self.id)

    def get_message_for_buyer(self):
        return "payment.neft.info.buyer"

    def get_message_for_seller(self):
        return "payment.neft.info.seller"

    def get_message_for_account_creation(self):
        return "payment.neft.info.account"
