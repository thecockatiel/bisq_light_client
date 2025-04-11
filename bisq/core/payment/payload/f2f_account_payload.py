from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
import pb_pb2 as protobuf

class F2FAccountPayload(CountryBasedPaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        contact: str = "",
        city: str = "",
        extra_info: str = "",
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
        self.contact = contact
        self.city = city
        self.extra_info = extra_info

    def to_proto_message(self):
        f2f_payload = protobuf.F2FAccountPayload(
            contact=self.contact,
            city=self.city,
            extra_info=self.extra_info
        )
        
        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.f2f_account_payload.CopyFrom(f2f_payload)

        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "F2FAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        f2f_payload = country_based_payload.f2f_account_payload
        
        return F2FAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.country_code,
            contact=f2f_payload.contact,
            city=f2f_payload.city,
            extra_info=f2f_payload.extra_info,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data)
        )
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        return (f"{Res.get(self.payment_method_id)} - "
                f"{Res.get_with_col('payment.f2f.contact')} {self.contact}, "
                f"{Res.get_with_col('payment.f2f.city')} {self.city}, "
                f"{Res.get_with_col('payment.shared.extraInfo')} {self.extra_info}")

    def get_payment_details_for_trade_popup(self) -> str:
        # We don't show here more as the makers extra data are the relevant for the trade.
        # City has to be anyway the same for maker and taker.
        return f"{Res.get_with_col('payment.f2f.contact')} {self.contact}"

    def show_ref_text_warning(self) -> bool:
        return False

    def get_age_witness_input_data(self) -> bytes:
        # We use here the city because the address alone seems to be too weak
        contact_bytes = self.contact.encode('utf-8')
        city_bytes = self.city.encode('utf-8')
        return self.get_age_witness_input_data_using_bytes(contact_bytes + city_bytes)

