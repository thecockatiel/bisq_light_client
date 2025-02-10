from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


# Cannot be deleted as it would break old trade history entries
# Removed due too high chargeback risk
class VenmoAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        venmo_user_name: str = None,
        holder_name: str = None,
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.venmo_user_name = venmo_user_name or ""
        self.holder_name = holder_name or ""

    def to_proto_message(self):
        venmo_payload = protobuf.VenmoAccountPayload(
            venmo_user_name=self.venmo_user_name,
            holder_name=self.holder_name,
        )

        builder = self.get_payment_account_payload_builder()
        builder.venmo_account_payload.CopyFrom(venmo_payload)
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        venmo_payload = proto.venmo_account_payload
        return VenmoAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            venmo_user_name=venmo_payload.venmo_user_name,
            holder_name=venmo_payload.holder_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        account_owner = Res.get_with_col("payment.account.owner")
        venmo_user = Res.get_with_col("payment.venmo.venmoUserName")

        return f"{payment_method} - {account_owner} {self.holder_name}, {venmo_user} {self.venmo_user_name}"

    def get_payment_details_for_trade_popup(self) -> str:
        return self.get_payment_details()

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.venmo_user_name.encode("utf-8")
        )

    @property
    def owner_id(self) -> bool:
        return self.holder_name
