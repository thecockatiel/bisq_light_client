from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class HalCashAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        mobile_nr: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.mobile_nr = mobile_nr

    def to_proto_message(self):
        payload = protobuf.HalCashAccountPayload(
            mobile_nr=self.mobile_nr,
        )

        builder = self.get_payment_account_payload_builder()
        builder.hal_cash_account_payload.CopyFrom(payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.hal_cash_account_payload
        return HalCashAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            mobile_nr=payload.mobile_nr,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        payment_mobile = Res.get_with_col("payment.mobile")
        return f"{payment_method} - {payment_mobile} {self.mobile_nr}"

    def get_payment_details_for_trade_popup(self) -> str:
        return Res.get_with_col("payment.mobile") + " " + self.mobile_nr

    def show_ref_text_warning(self):
        return False

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.mobile_nr.encode("utf-8")
        )
