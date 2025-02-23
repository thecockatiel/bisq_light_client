from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class FasterPaymentsAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        sort_code: str = "",
        account_nr: str = "",
        email: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.sort_code = sort_code
        self.account_nr = account_nr
        # email not used anymore but need to keep it for backward compatibility, must not be null but empty string, otherwise hash check fails for contract
        self.email = email or ""

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.faster_payments_account_payload.CopyFrom(
            protobuf.FasterPaymentsAccountPayload(
                sort_code=self.sort_code,
                account_nr=self.account_nr,
                email=self.email,
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.faster_payments_account_payload
        return FasterPaymentsAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            sort_code=payload.sort_code,
            account_nr=payload.account_nr,
            email=payload.email,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        return (
            Res.get(self.payment_method_id)
            + " - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )

    def get_payment_details_for_trade_popup(self) -> str:
        return (
            (
                f"{Res.get('payment.account.owner.fullname')}: {self.holder_name}\n"
                if self.holder_name
                else ""
            )
            + f"UK Sort code: {self.sort_code}\n"
            + f"{Res.get('payment.accountNr')}: {self.account_nr}"
        )

    def get_age_witness_input_data(self) -> bytes:
        return super().get_age_witness_input_data(
            self.sort_code.encode("utf-8") + self.account_nr.encode("utf-8")
        )
