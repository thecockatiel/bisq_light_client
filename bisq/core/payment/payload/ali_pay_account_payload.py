from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class AliPayAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        account_nr: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.account_nr = account_nr

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.ali_pay_account_payload.CopyFrom(
            protobuf.AliPayAccountPayload(
                account_nr=self.account_nr,
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.ali_pay_account_payload
        return AliPayAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            account_nr=payload.account_nr,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        label = Res.get_with_col("payment.account.no")
        return f"{payment_method} - {label} {self.account_nr}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.account_nr.encode("utf-8")
        )
