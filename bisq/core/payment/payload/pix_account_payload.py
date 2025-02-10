from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class PixAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str,
        pix_key: str = "",
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
        self.pix_key = pix_key or ""

    def to_proto_message(self):
        pix_payload = protobuf.PixAccountPayload(
            pix_key=self.pix_key,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.pix_account_payload.CopyFrom(
            pix_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "PixAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        pix_payload = country_based_payload.pix_account_payload

        return PixAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.countryCode,
            pix_key=pix_payload.pix_key,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        payment_details = self.get_payment_details_for_trade_popup().replace("\n", ", ")
        return f"{payment_method} - {payment_details}"

    def get_payment_details_for_trade_popup(self) -> str:
        pix_key_label = Res.get_with_col("payment.pix.key")
        owner_label = Res.get_with_col("payment.account.owner")
        holder_name = self.get_holder_name_or_prompt_if_empty()
        return f"{pix_key_label} {self.pix_key}\n{owner_label} {holder_name}"

    def get_age_witness_input_data(self) -> bytes:
        # holderName will be included as part of the witness data.
        # older accounts that don't have holderName still retain their existing witness.
        pix_key_bytes = self.pix_key.encode("utf-8")
        holder_name_bytes = self.holder_name.encode("utf-8")
        return super().get_age_witness_input_data(pix_key_bytes + holder_name_bytes)
