from bisq.core.payment.ifsc_based_account import IfscBasedAccount
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.paytm_account_payload import PaytmAccountPayload


class PaytmAccount(IfscBasedAccount):

    def __init__(self):
        super().__init__(PaymentMethod.PAYTM)

    def create_payload(self) -> PaymentAccountPayload:
        return PaytmAccountPayload(self.payment_method.id, self.id)

    @property
    def email_or_mobile_nr(self) -> str:
        return self._paytm_account_payload.email_or_mobile_nr

    @email_or_mobile_nr.setter
    def email_or_mobile_nr(self, value: str):
        if value is None:
            value = ""
        self._paytm_account_payload.email_or_mobile_nr = value

    def get_message_for_buyer(self) -> str:
        return "payment.paytm.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.paytm.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.paytm.info.account"

    @property
    def _paytm_account_payload(self):
        assert isinstance(self.payment_account_payload, PaytmAccountPayload)
        return self.payment_account_payload
