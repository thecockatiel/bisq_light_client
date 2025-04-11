from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class UpiAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        virtual_payment_address: str = "",
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
        self.virtual_payment_address = virtual_payment_address

    def to_proto_message(self):
        upi_payload = protobuf.UpiAccountPayload(
            virtual_payment_address=self.virtual_payment_address,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.upi_account_payload.CopyFrom(
            upi_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "UpiAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        upi_payload = country_based_payload.upi_account_payload

        return UpiAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.country_code,
            virtual_payment_address=upi_payload.virtual_payment_address,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        detail_label = Res.get_with_col("payment.upi.virtualPaymentAddress")
        return f"{payment_method} - {detail_label} {self.virtual_payment_address}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.virtual_payment_address.encode("utf-8")
        )
