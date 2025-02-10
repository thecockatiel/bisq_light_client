from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class MoneyBeamAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        account_id: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.account_id = account_id

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.money_beam_account_payload.CopyFrom(
            protobuf.MoneyBeamAccountPayload(
                account_id=self.account_id,
            )
        )

        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "MoneyBeamAccountPayload":
        payload = proto.money_beam_account_payload

        return MoneyBeamAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            account_id=payload.account_id,
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
        account_res = Res.get_with_col("payment.account")
        owner_res = Res.get_with_col("payment.account.owner")
        holder_name = self.get_holder_name_or_prompt_if_empty()
        return f"{account_res} {self.account_id}\n{owner_res} {holder_name}"

    def get_age_witness_input_data(self) -> bytes:
        # holderName will be included as part of the witness data.
        # older accounts that don't have holderName still retain their existing witness.
        return self.get_age_witness_input_data_using_bytes(
            self.account_id.encode("utf-8") + self.holder_name.encode("utf-8")
        )
