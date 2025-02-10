from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class TikkieAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        iban: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            country_code,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.iban = iban

    def to_proto_message(self):
        tikkie_payload = protobuf.TikkieAccountPayload(
            iban=self.iban,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.tikkie_account_payload.CopyFrom(
            tikkie_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "TikkieAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        tikkie_payload = country_based_payload.tikkie_account_payload

        return TikkieAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.countryCode,
            iban=tikkie_payload.iban,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        iban_label = Res.get_with_col("payment.iban")
        return f"{payment_method} - {iban_label} {self.iban}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(self.iban.encode("utf-8"))
