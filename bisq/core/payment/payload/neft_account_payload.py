from typing import Union
from bisq.core.locale.res import Res
from bisq.core.payment.payload.ifsc_based_account_payload import IfscBasedAccountPayload
import pb_pb2 as protobuf

class NeftAccountPayload(IfscBasedAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str,
        holder_name: str = "",
        account_nr: str = "",
        ifsc: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Union[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            country_code,
            holder_name,
            account_nr,
            ifsc,
            max_trade_period,
            exclude_from_json_data_map,
        )

    def to_proto_message(self):
        ifsc_based_account_payload_builder = self.get_payment_account_payload_builder()
        ifsc_based_account_payload_builder.country_based_payment_account_payload.ifsc_based_account_payload.neft_account_payload.CopyFrom(
            protobuf.NeftAccountPayload()
        )
        return ifsc_based_account_payload_builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        country_based_payment_account_payload = (
            proto.country_based_payment_account_payload
        )
        ifsc_based_account_payload = (
            country_based_payment_account_payload.ifsc_based_account_payload
        )
        return NeftAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payment_account_payload.countryCode,
            holder_name=ifsc_based_account_payload.holder_name,
            account_nr=ifsc_based_account_payload.account_nr,
            ifsc=ifsc_based_account_payload.ifsc,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        account_owner = Res.get_with_col("payment.account.owner")
        account_no = Res.get_with_col("payment.account.no")
        ifsc_code = Res.get_with_col("payment.ifsc")

        return f"{payment_method} - {account_owner} {self.holder_name}, {account_no} {self.account_nr}, {ifsc_code} {self.ifsc}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        account_nr = self.account_nr if self.account_nr is not None else ""
        return self.get_age_witness_input_data_using_bytes(account_nr.encode("utf-8"))
