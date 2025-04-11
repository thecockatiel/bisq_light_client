from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class SatispayAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: str = "",
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
        self._holder_name = holder_name
        self.mobile_nr = mobile_nr

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        satispay_payload = protobuf.SatispayAccountPayload(
            mobile_nr=self.mobile_nr,
            holder_name=self.holder_name,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.satispay_account_payload.CopyFrom(
            satispay_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "SatispayAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        satispay_payload = country_based_payload.satispay_account_payload

        return SatispayAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.country_code,
            holder_name=satispay_payload.holder_name,
            mobile_nr=satispay_payload.mobile_nr,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        user_name_label = Res.get_with_col("payment.account.userName")
        return f"{payment_method} - {user_name_label} {self.holder_name}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.holder_name.encode("utf-8")
        )
