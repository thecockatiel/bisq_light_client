from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class PromptPayAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        prompt_pay_id: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.prompt_pay_id = prompt_pay_id

    def to_proto_message(self):
        payload = protobuf.PromptPayAccountPayload(
            prompt_pay_id=self.prompt_pay_id,
        )

        builder = self.get_payment_account_payload_builder()
        builder.prompt_pay_account_payload.CopyFrom(payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.prompt_pay_account_payload
        return PromptPayAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            prompt_pay_id=payload.prompt_pay_id,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        return (
            Res.get_with_col("payment.promptPay.promptPayId") + " " + self.prompt_pay_id
        )

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.prompt_pay_id.encode("utf-8")
        )
