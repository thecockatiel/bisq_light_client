from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class AustraliaPayidAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_id: str,
        id: str,
        payid: str = "",
        bank_account_name: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_id, id, max_trade_period, exclude_from_json_data_map
        )
        self.payid = payid
        self.bank_account_name = bank_account_name

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.australia_payid_payload.CopyFrom(
            protobuf.AustraliaPayidPayload(
                payid=self.payid,
                bank_account_name=self.bank_account_name,
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        payload = proto.australia_payid_payload
        return AustraliaPayidAccountPayload(
            payment_method_id=proto.payment_method_id,
            id=proto.id,
            payid=payload.payid,
            bank_account_name=payload.bank_account_name,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        return (
            Res.get(self.payment_method_id)
            + " - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )

    def get_payment_details_for_trade_popup(self) -> str:
        return (
            f"{Res.get('payment.australia.payid')}: {self.payid}\n"
            f"{Res.get('payment.account.owner.fullname')}: {self.bank_account_name}"
        )

    def get_age_witness_input_data(self) -> bytes:
        all = self.payid + self.bank_account_name
        return self.get_age_witness_input_data_using_bytes(all.encode("utf-8"))
