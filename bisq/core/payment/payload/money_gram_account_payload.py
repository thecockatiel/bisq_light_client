from typing import Optional
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
        country_code: str = None,
        holder_name: str = None,
        state: str = None,
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
        self.holder_name = holder_name or ""
        self.country_code = country_code or ""
        self.state = state or ""
        self.email = email

    def to_proto_message(self):
        money_gram_account_payload = protobuf.MoneyGramAccountPayload(
            holder_name=self.holder_name,
            country_code=self.country_code,
            state=self.state,
            email=self.email,
        )

        payload = self.get_payment_account_payload_builder()
        payload.money_gram_account_payload.CopyFrom(money_gram_account_payload)

        return payload

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
