from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.bank_util import BankUtil
from bisq.core.locale.country_util import get_name_by_code
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
import pb_pb2 as protobuf


class WesternUnionAccountPayload(
    CountryBasedPaymentAccountPayload, PayloadWithHolderName
):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: Optional[str] = None,
        city: Optional[str] = None,
        state: str = "",
        email: Optional[str] = None,
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
        self.city = city
        self.state = state
        self.email = email

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        wu_payload = protobuf.WesternUnionAccountPayload(
            holder_name=self.holder_name,
            city=self.city,
            state=self.state,
            email=self.email,
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.western_union_account_payload.CopyFrom(
            wu_payload
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "WesternUnionAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        wu_payload = country_based_payload.western_union_account_payload

        return WesternUnionAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.country_code,
            holder_name=wu_payload.holder_name,
            city=wu_payload.city,
            state=wu_payload.state,
            email=wu_payload.email,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        details = self.get_payment_details_for_trade_popup().replace("\n", ", ")
        return f"{payment_method} - {details}"

    def get_payment_details_for_trade_popup(self) -> str:
        city_state = (
            f"{Res.get('payment.account.city')} / {Res.get_with_col('payment.account.state')} {self.city} / {self.state}\n"
            if BankUtil.is_state_required(self.country_code)
            else f"{Res.get_with_col('payment.account.city')} {self.city}\n"
        )
        return (
            f"{Res.get_with_col('payment.account.fullName')} {self.holder_name}\n"
            f"{city_state}"
            f"{Res.get_with_col('payment.country')} {get_name_by_code(self.country_code)}\n"
            f"{Res.get_with_col('payment.email')} {self.email}"
        )

    def show_ref_text_warning(self):
        return False

    def get_age_witness_input_data(self) -> bytes:
        all_data = self.country_code + self.holder_name + self.email
        return self.get_age_witness_input_data_using_bytes(all_data.encode("utf-8"))
