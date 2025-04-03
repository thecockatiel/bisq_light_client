from bisq.core.payment.ifsc_based_account import IfscBasedAccount
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.rtgs_account_payload import RtgsAccountPayload


class RtgsAccount(IfscBasedAccount):

    def __init__(self):
        super().__init__(PaymentMethod.RTGS)

    def create_payload(self) -> PaymentAccountPayload:
        return RtgsAccountPayload(self.payment_method.id, self.id)

    def get_message_for_buyer(self) -> str:
        return "payment.rtgs.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.rtgs.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.rtgs.info.account"
