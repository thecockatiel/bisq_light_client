from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import proto.pb_pb2 as protobuf

class AmazonGiftCardAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        email_or_mobile_nr: Optional[str] = None,
        country_code: Optional[str] = None,
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(payment_method_id, id, max_trade_period, exclude_from_json_data_map)
        self.email_or_mobile_nr = email_or_mobile_nr
        # For backward compatibility we need to exclude the new field for the contract json.
        # We can remove that after a while when risk that users with pre 1.5.5 version is very low.
        self.country_code = country_code  # JsonExclude

    def get_json_dict(self):
        self_dict = self.__dict__.copy()
        self_dict.pop("country_code")
        return self_dict

    def to_proto_message(self):
        amazon_payload = protobuf.AmazonGiftCardAccountPayload(
            country_code=self.country_code,
            email_or_mobile_nr=self.email_or_mobile_nr,
        )
        
        builder = self.get_payment_account_payload_builder()
        builder.amazon_gift_card_account_payload.CopyFrom(amazon_payload)
        return builder
    
    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        amazon_payload = proto.amazon_gift_card_account_payload
        return AmazonGiftCardAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            email_or_mobile_nr=amazon_payload.email_or_mobile_nr,
            country_code=amazon_payload.country_code,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),            
        )

    def get_payment_details(self) -> str:
        return f"{Res.get(self.payment_method_id)} - {self.get_payment_details_for_trade_popup().replace('\n', ', ')}"

    def get_payment_details_for_trade_popup(self) -> str:
        return f"{Res.get_with_col('payment.email.mobile')} {self.email_or_mobile_nr}"

    def get_age_witness_input_data(self) -> bytes:
        data = f"AmazonGiftCard{self.email_or_mobile_nr}"
        return self.get_age_witness_input_data_using_bytes(data.encode('utf-8'))

    @property
    def country_not_set(self) -> bool:
        return not self.country_code

