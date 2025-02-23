from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class SbpAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        holder_name: str = "",
        mobile_number: str = "",
        bank_name: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self._holder_name = holder_name
        self.mobile_number = mobile_number
        self.bank_name = bank_name

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.sbp_account_payload.CopyFrom(
            protobuf.SbpAccountPayload(
                holder_name=self.holder_name,
                mobile_number=self.mobile_number,
                bank_name=self.bank_name,
            )
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "SbpAccountPayload":
        payload = proto.sbp_account_payload

        return SbpAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            holder_name=payload.holder_name,
            mobile_number=payload.mobile_number,
            bank_name=payload.bank_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        account_owner = Res.get_with_col("payment.account.owner.name")
        mobile_label = Res.get_with_col("payment.mobile")
        bank_label = Res.get_with_col("payment.bank.name")

        return (
            f"{payment_method} - "
            f"{account_owner} {self.holder_name}, "
            f"{mobile_label} {self.mobile_number}, "
            f"{bank_label} {self.bank_name}"
        )

    def get_payment_details_for_trade_popup(self) -> str:
        holder_name_label = Res.get_with_col("payment.account.owner.name")
        mobile_label = Res.get_with_col("payment.mobile")
        bank_label = Res.get_with_col("payment.bank.name")

        return (
            f"{holder_name_label} {self.holder_name}\n"
            f"{mobile_label} {self.mobile_number}\n"
            f"{bank_label} {self.bank_name}"
        )

    def get_age_witness_input_data(self) -> bytes:
        # We don't add holderName because we don't want to break age validation if the user recreates an account with
        # slight changes in holder name (e.g. add or remove middle name)
        mobile_number = self.mobile_number.encode("utf-8")
        bank_name = self.bank_name.encode("utf-8")
        return self.get_age_witness_input_data_using_bytes(mobile_number + bank_name)

    @property
    def owner_id(self) -> str:
        return self.holder_name
