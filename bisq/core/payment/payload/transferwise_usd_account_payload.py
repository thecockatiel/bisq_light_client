from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf


class TransferwiseUsdAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str,
        email: str = "",
        holder_name: str = "",
        beneficiary_address: str = "",
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
        self.email = email or ""
        self._holder_name = holder_name or ""
        self.beneficiary_address = beneficiary_address or ""

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        transferwise_payload = protobuf.TransferwiseUsdAccountPayload(
            email=self.email,
            holder_name=self.holder_name,
            beneficiary_address=self.beneficiary_address,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.transferwise_usd_account_payload.CopyFrom(
            transferwise_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "TransferwiseUsdAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        transferwise_payload = country_based_payload.transferwise_usd_account_payload

        return TransferwiseUsdAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.countryCode,
            email=transferwise_payload.email,
            holder_name=transferwise_payload.holder_name,
            beneficiary_address=transferwise_payload.beneficiary_address,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method_id_label = Res.get(self.payment_method_id)
        user_name_label = Res.get_with_col("payment.account.userName")
        return f"{payment_method_id_label} - {user_name_label} {self.holder_name}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.holder_name.encode("utf-8")
        )
