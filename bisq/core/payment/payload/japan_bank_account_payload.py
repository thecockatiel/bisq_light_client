from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class JapanBankAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        bank_name: str = "",
        bank_code: str = "",
        bank_branch_name: str = "",
        bank_branch_code: str = "",
        bank_account_type: str = "",
        bank_account_name: str = "",
        bank_account_number: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            max_trade_period,
            exclude_from_json_data_map,
        )
        # bank
        self.bank_name = bank_name
        self.bank_code = bank_code
        # branch
        self.bank_branch_name = bank_branch_name
        self.bank_branch_code = bank_branch_code
        # account
        self.bank_account_type = bank_account_type
        self.bank_account_name = bank_account_name
        self.bank_account_number = bank_account_number

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.japan_bank_account_payload.CopyFrom(
            protobuf.JapanBankAccountPayload(
                bank_name=self.bank_name,
                bank_code=self.bank_code,
                bank_branch_name=self.bank_branch_name,
                bank_branch_code=self.bank_branch_code,
                bank_account_type=self.bank_account_type,
                bank_account_name=self.bank_account_name,
                bank_account_number=self.bank_account_number,
            )
        )

        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "JapanBankAccountPayload":
        payload = proto.japan_bank_account_payload

        return JapanBankAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            bank_name=payload.bank_name,
            bank_code=payload.bank_code,
            bank_branch_name=payload.bank_branch_name,
            bank_branch_code=payload.bank_branch_code,
            bank_account_type=payload.bank_account_type,
            bank_account_name=payload.bank_account_name,
            bank_account_number=payload.bank_account_number,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        return (
            Res.get(self.payment_method_id)
            + " - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )

    def get_payment_details_for_trade_popup(self) -> str:
        bank_details = (
            f"{Res.get('payment.japan.bank')}: {self.bank_name}({self.bank_code})"
        )
        branch_details = f"{Res.get('payment.japan.branch')}: {self.bank_branch_name}({self.bank_branch_code})"
        account_details = f"{Res.get('payment.japan.account')}: {self.bank_account_type} {self.bank_account_number}"
        recipient_details = (
            f"{Res.get('payment.japan.recipient')}: {self.bank_account_name}"
        )

        return (
            f"{bank_details}\n{branch_details}\n{account_details}\n{recipient_details}"
        )

    def get_age_witness_input_data(self) -> bytes:
        all_data = (
            self.bank_name
            + self.bank_branch_name
            + self.bank_account_type
            + self.bank_account_number
            + self.bank_account_name
        )
        return super().get_age_witness_input_data(all_data.encode("utf-8"))

    @property
    def holder_name(self) -> str:
        return self.bank_account_name
