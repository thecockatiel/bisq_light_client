from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class VerseAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        holder_name: str = None,
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.holder_name = holder_name or ""

    def to_proto_message(self):
        verse_payload = protobuf.VerseAccountPayload(
            holder_name=self.holder_name,
        )

        builder = self.get_payment_account_payload_builder()
        builder.verse_account_payload.CopyFrom(verse_payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        verse_payload = proto.verse_account_payload
        return VerseAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            holder_name=verse_payload.holder_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        details_label = Res.get_with_col("payment.account.userName")
        return f"{payment_method} - {details_label} {self.holder_name}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.holder_name.encode("utf-8")
        )
