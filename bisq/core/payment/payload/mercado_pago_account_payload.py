from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class MercadoPagoAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        account_holder_name: str = "",
        account_holder_id: str = "",
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
        self.account_holder_name = account_holder_name
        self.account_holder_id = account_holder_id

    def to_proto_message(self):
        mercado_payload = protobuf.MercadoPagoAccountPayload(
            holder_name=self.account_holder_name,
            holder_id=self.account_holder_id,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.mercado_pago_account_payload.CopyFrom(
            mercado_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "MercadoPagoAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        mercado_payload = country_based_payload.mercado_pago_account_payload

        return MercadoPagoAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.country_code,
            account_holder_name=mercado_payload.holder_name,
            account_holder_id=mercado_payload.holder_id,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        payment_details = self.get_payment_details_for_trade_popup().replace("\n", ", ")
        return f"{payment_method} - {payment_details}"

    def get_payment_details_for_trade_popup(self) -> str:
        holder_id_label = Res.get("payment.mercadoPago.holderId")
        owner_label = Res.get("payment.account.owner.fullname")
        return (
            f"{holder_id_label}: {self.account_holder_id}\n"
            f"{owner_label}: {self.account_holder_name}"
        )

    def get_age_witness_input_data(self) -> bytes:
        all_data = self.account_holder_id + self.account_holder_name
        return self.get_age_witness_input_data_using_bytes(all_data.encode("utf-8"))
