from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class NequiAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        mobile_nr: str = "",
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
        self.mobile_nr = mobile_nr

    def to_proto_message(self):
        nequi_payload = protobuf.NequiAccountPayload(
            mobile_nr=self.mobile_nr,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.nequi_account_payload.CopyFrom(
            nequi_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "NequiAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        nequi_payload = country_based_payload.nequi_account_payload

        return NequiAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.countryCode,
            mobile_nr=nequi_payload.mobile_nr,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        mobile_label = Res.get_with_col("payment.mobile")
        return f"{payment_method} - {mobile_label} {self.mobile_nr}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.mobile_nr.encode("utf-8")
        )
