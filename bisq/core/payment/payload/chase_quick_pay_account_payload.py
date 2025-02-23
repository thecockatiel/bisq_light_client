from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


# Removed due to QuickPay becoming Zelle
# Cannot be deleted as it would break old trade history entries
class ChaseQuickPayAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        email: str = "",
        holder_name: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.email = email
        self._holder_name = holder_name

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.chase_quick_pay_account_payload.CopyFrom(
            protobuf.ChaseQuickPayAccountPayload(
                email=self.email,
                holder_name=self.holder_name,
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "ChaseQuickPayAccountPayload":
        payload = proto.chase_quick_pay_account_payload

        return ChaseQuickPayAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            email=payload.email,
            holder_name=payload.holder_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        return (
            f"{Res.get(self.payment_method_id)} - "
            f"{Res.get_with_col('payment.account.owner.fullname')} {self.holder_name}, "
            f"{Res.get('payment.email')} {self.email}"
        )

    def get_payment_details_for_trade_popup(self) -> str:
        return (
            f"{Res.get_with_col('payment.account.owner.fullname')} {self.holder_name}\n"
            f"{Res.get_with_col('payment.email')} {self.email}"
        )

    def get_age_witness_input_data(self) -> bytes:
        # We don't add holderName because we don't want to break age validation if the user recreates an account with
        # slight changes in holder name (e.g. add or remove middle name)
        return self.get_age_witness_input_data_using_bytes(self.email.encode("utf-8"))

    @property
    def owner_id(self) -> str:
        return self.holder_name
