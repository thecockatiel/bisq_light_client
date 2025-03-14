from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.rtgs_account_payload import RtgsAccountPayload
from bisq.core.payment.payment_account import IfscBasedAccount


class RtgsAccount(IfscBasedAccount):
    def __init__(self):
        super().__init__(PaymentMethod.RTGS)

    def create_payload(self):
        return RtgsAccountPayload(self.payment_method.id, self.id)

    def get_message_for_buyer(self):
        return "payment.rtgs.info.buyer"

    def get_message_for_seller(self):
        return "payment.rtgs.info.seller"

    def get_message_for_account_creation(self):
        return "payment.rtgs.info.account"
