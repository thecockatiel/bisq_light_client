from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class InteracETransferAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        email: str = "",
        holder_name: str = "",
        question: str = "",
        answer: str = "",
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
        self.question = question
        self.answer = answer

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.interac_e_transfer_account_payload.CopyFrom(
            protobuf.InteracETransferAccountPayload(
                email=self.email,
                holder_name=self.holder_name,
                question=self.question,
                answer=self.answer,
            )
        )

        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.PaymentAccountPayload,
    ) -> "InteracETransferAccountPayload":
        payload = proto.interac_e_transfer_account_payload

        return InteracETransferAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            email=payload.email,
            holder_name=payload.holder_name,
            question=payload.question,
            answer=payload.answer,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_details(self) -> str:
        payment_method = Res.get(self.payment_method_id)
        account_owner = Res.get_with_col("payment.account.owner.fullname")
        email_label = Res.get("payment.email")
        secret_label = Res.get_with_col("payment.secret")
        answer_label = Res.get_with_col("payment.answer")

        return (
            f"{payment_method} - {account_owner} {self.holder_name}, "
            f"{email_label} {self.email}, {secret_label} {self.question}, "
            f"{answer_label} {self.answer}"
        )

    def get_payment_details_for_trade_popup(self) -> str:
        return (
            f"{Res.get_with_col('payment.account.owner.fullname')} {self.holder_name}\n"
            f"{Res.get_with_col('payment.email')} {self.email}\n"
            f"{Res.get_with_col('payment.secret')} {self.question}\n"
            f"{Res.get_with_col('payment.answer')} {self.answer}"
        )

    def get_age_witness_input_data(self) -> bytes:
        email_bytes = self.email.encode("utf-8")
        question_bytes = self.question.encode("utf-8")
        answer_bytes = self.answer.encode("utf-8")
        return self.get_age_witness_input_data_using_bytes(
            email_bytes + question_bytes + answer_bytes
        )

    @property
    def owner_id(self) -> str:
        return self.holder_name
