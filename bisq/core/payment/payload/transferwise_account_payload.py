from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class TransferwiseAccountPayload(PaymentAccountPayload):

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
        payload = protobuf.TransferwiseAccountPayload(
            email=self.email,
        )
        builder = self.get_payment_account_payload_builder()
        builder.transferwise_account_payload.CopyFrom(payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.transferwise_account_payload
        return TransferwiseAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            email=payload.email,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        return (
            Res.get(self.payment_method_id)
            + " - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )

    def get_payment_details_for_trade_popup(self) -> str:
        email_label = Res.get_with_col("payment.email")
        owner_label = Res.get_with_col("payment.account.owner.fullname")
        holder_name = self.get_holder_name_or_prompt_if_empty()
        return f"{email_label} {self.email}\n{owner_label} {holder_name}"

    def get_age_witness_input_data(self) -> bytes:
        # // holderName will be included as part of the witness data.
        # // older accounts that don't have holderName still retain their existing witness.
        return self.get_age_witness_input_data_using_bytes(
            self.email.encode("utf-8") + self.holder_name.encode("utf-8")
        )
