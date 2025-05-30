from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class CelPayAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        email: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.email = email

    def to_proto_message(self):
        payload = protobuf.CelPayAccountPayload(
            email=self.email,
        )
        builder = self.get_payment_account_payload_builder()
        builder.cel_pay_account_payload.CopyFrom(payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.cel_pay_account_payload
        return CelPayAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            email=payload.email,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        email = Res.get_with_col("payment.email")
        return f"{payment_method} - {email} {self.email}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(self.email.encode("utf-8"))
