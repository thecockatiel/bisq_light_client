from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


# Cannot be deleted as it would break old trade history entries
# Removed due too high chargeback risk
class CashAppAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        cash_tag: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.cash_tag = cash_tag

    def to_proto_message(self):
        cash_app_payload = protobuf.CashAppAccountPayload(
            cash_tag=self.cash_tag,
        )

        builder = self.get_payment_account_payload_builder()
        builder.cash_app_account_payload.CopyFrom(cash_app_payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        cash_app_payload = proto.cash_app_account_payload
        return CashAppAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            cash_tag=cash_app_payload.cash_tag,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        payment_account = Res.get_with_col("payment.account")
        return f"{payment_method} - {payment_account} {self.cash_tag}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.cash_tag.encode("utf-8")
        )
