from bisq.core.payment.ifsc_based_account import IfscBasedAccount
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.upi_account_payload import UpiAccountPayload


class UpiAccount(IfscBasedAccount):

    def __init__(self):
        super().__init__(PaymentMethod.UPI)

    def create_payload(self) -> PaymentAccountPayload:
        return UpiAccountPayload(self.payment_method.id, self.id)

    @property
    def virtual_payment_address(self) -> str:
        return self._upi_account_payload.virtual_payment_address

    @virtual_payment_address.setter
    def virtual_payment_address(self, value: str):
        if value is None:
            value = ""
        self._upi_account_payload.virtual_payment_address = value

    def get_message_for_buyer(self) -> str:
        return "payment.upi.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.upi.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.upi.info.account"

    @property
    def _upi_account_payload(self):
        assert isinstance(self.payment_account_payload, UpiAccountPayload)
        return self.payment_account_payload
