from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


# Cannot be deleted as it would break old trade history entries
class OKPayAccountPayload(PaymentAccountPayload):

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
        ok_payload = protobuf.OKPayAccountPayload(
            account_nr=self.account_nr,
        )

        builder = self.get_payment_account_payload_builder()
        builder.o_k_pay_account_payload.CopyFrom(ok_payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        okpay_app_payload = proto.o_k_pay_account_payload
        return OKPayAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            account_nr=okpay_app_payload.account_nr,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        payment_account = Res.get_with_col("payment.account.no")
        return f"{payment_method} - {payment_account} {self.account_nr}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.account_nr.encode("utf-8")
        )
