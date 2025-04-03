from bisq.core.payment.ifsc_based_account import IfscBasedAccount
from bisq.core.payment.payload.neft_account_payload import NeftAccountPayload
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod


class NeftAccount(IfscBasedAccount):

    def __init__(self):
        super().__init__(PaymentMethod.NEFT)

    def create_payload(self) -> PaymentAccountPayload:
        return NeftAccountPayload(self.payment_method.id, self.id)

    def get_message_for_buyer(self) -> str:
        return "payment.neft.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.neft.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.neft.info.account"
