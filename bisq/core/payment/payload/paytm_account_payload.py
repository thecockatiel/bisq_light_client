from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class PaytmAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        email_or_mobile_nr: str = "",
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
        self.email_or_mobile_nr = email_or_mobile_nr

    def to_proto_message(self):
        paytm_payload = protobuf.PaytmAccountPayload(
            email_or_mobile_nr=self.email_or_mobile_nr,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.paytm_account_payload.CopyFrom(
            paytm_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "PaytmAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        paytm_payload = country_based_payload.paytm_account_payload

        return PaytmAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.country_code,
            email_or_mobile_nr=paytm_payload.email_or_mobile_nr,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        mobile_label = Res.get_with_col("payment.email.mobile")
        return f"{payment_method} - {mobile_label} {self.email_or_mobile_nr}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.email_or_mobile_nr.encode("utf-8")
        )
