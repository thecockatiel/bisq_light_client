from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import proto.pb_pb2 as protobuf

class CashByMailAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        postal_address: str = "",
        contact: str = "",
        extra_info: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: dict[str, str] | None = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.postal_address = postal_address or ""
        self.contact = contact or ""
        self.extra_info = extra_info or ""

    def to_proto_message(self):
        cash_by_mail_payload = protobuf.CashByMailAccountPayload(
            postal_address=self.postal_address,
            contact=self.contact,
            extra_info=self.extra_info
        )
        
        payload = self.get_payment_account_payload_builder()
        payload.cash_by_mail_account_payload.CopyFrom(cash_by_mail_payload)
        
        return payload

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "CashByMailAccountPayload":
        cash_by_mail_payload = proto.cash_by_mail_account_payload
        
        return CashByMailAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            postal_address=cash_by_mail_payload.postal_address,
            contact=cash_by_mail_payload.contact,
            extra_info=cash_by_mail_payload.extra_info,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data)
        )
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        return f"{Res.get(self.payment_method_id)} - {Res.get_with_col('payment.account.owner')} {self.contact}, " \
               f"{Res.get_with_col('payment.postal.address')} {self.postal_address}, " \
               f"{Res.get_with_col('payment.shared.extraInfo')} {self.extra_info}"

    def get_payment_details_for_trade_popup(self) -> str:
        return f"{Res.get_with_col('payment.account.owner')} {self.contact}\n" \
               f"{Res.get_with_col('payment.postal.address')} {self.postal_address}"

    def show_ref_text_warning(self) -> bool:
        return False

    def get_age_witness_input_data(self) -> bytes:
        # We use here the contact because the address alone seems to be too weak
        contact_bytes = self.contact.encode('utf-8')
        address_bytes = self.postal_address.encode('utf-8')
        return super().get_age_witness_input_data(contact_bytes + address_bytes)

    def get_owner_id(self) -> str:
        return self.contact

    def get_holder_name(self) -> str:
        return self.contact


