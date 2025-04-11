from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class ClearXchangeAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        email_or_mobile_nr: str = "",
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
        self.email_or_mobile_nr = email_or_mobile_nr
        self._holder_name = holder_name

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.clear_xchange_account_payload.CopyFrom(
            protobuf.ClearXchangeAccountPayload(
                holder_name=self.holder_name,
                email_or_mobile_nr=self.email_or_mobile_nr,
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "ClearXchangeAccountPayload":
        payload = proto.clear_xchange_account_payload

        return ClearXchangeAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            email_or_mobile_nr=payload.email_or_mobile_nr,
            holder_name=payload.holder_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        return (
            f"{Res.get(self.payment_method_id)} - "
            f"{Res.get_with_col('payment.account.owner.fullname')} {self.holder_name}, "
            f"{Res.get_with_col('payment.emailOrMobile')} {self.email_or_mobile_nr}"
        )

    def get_payment_details_for_trade_popup(self) -> str:
        return (
            f"{Res.get_with_col('payment.account.owner.fullname')} {self.holder_name}\n"
            f"{Res.get_with_col('payment.emailOrMobile')} {self.email_or_mobile_nr}"
        )

    def get_age_witness_input_data(self) -> bytes:
        # We don't add holderName because we don't want to break age validation if the user recreates an account with
        # slight changes in holder name (e.g. add or remove middle name)
        return self.get_age_witness_input_data_using_bytes(
            self.email_or_mobile_nr.encode("utf-8")
        )

    @property
    def owner_id(self) -> str:
        return self.holder_name
