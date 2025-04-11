from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.bank_util import BankUtil
from bisq.core.locale.country_util import get_name_by_code
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class MoneyGramAccountPayload(PaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: Optional[str] = None,
        state: str = "",
        email: Optional[str] = None,
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
        self.country_code = country_code
        self.state = state
        self.email = email

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.money_gram_account_payload.CopyFrom(
            protobuf.MoneyGramAccountPayload(
                holder_name=self.holder_name,
                country_code=self.country_code,
                state=self.state,
                email=self.email,
            )
        )

        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "MoneyGramAccountPayload":
        money_gram_account_payload = proto.money_gram_account_payload

        return MoneyGramAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=money_gram_account_payload.country_code,
            holder_name=money_gram_account_payload.holder_name,
            state=money_gram_account_payload.state,
            email=money_gram_account_payload.email,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
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
        if BankUtil.is_state_required(self.country_code):
            state = Res.get_with_col("payment.account.state") + " " + self.state + "\n"
        else:
            state = self.state
        return (
            Res.get_with_col("payment.account.full_name")
            + " "
            + self.holder_name
            + "\n"
            + state
            + Res.get_with_col("payment.bank.country")
            + " "
            + get_name_by_code(self.country_code)
            + "\n"
            + Res.get_with_col("payment.email")
            + " "
            + self.email
        )

    def show_ref_text_warning(self) -> bool:
        return False

    def get_age_witness_input_data(self) -> bytes:
        all_data = self.country_code + self.state + self.holder_name + self.email
        return self.get_age_witness_input_data_using_bytes(all_data.encode("utf-8"))
