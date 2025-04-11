from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
import pb_pb2 as protobuf


class UpholdAccountPayload(PaymentAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        account_id: str = "",
        account_owner: str = "",
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
        # For backward compatibility we need to exclude the new field from the contract json.
        self.account_owner = account_owner

    def get_json_dict(self):
        result = super().get_json_dict()
        result.pop("accountOwner", None)
        return result

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.uphold_account_payload.CopyFrom(
            protobuf.UpholdAccountPayload(
                account_id=self.account_id,
                account_owner=self.account_owner,
            )
        )

        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "UpholdAccountPayload":
        payload = proto.uphold_account_payload

        return UpholdAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            account_id=payload.account_id,
            account_owner=payload.account_owner,
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
        if not self.account_owner:
            return (
                f"{Res.get('payment.account')}: {self.account_id}\n"
                f"{Res.get('payment.account.owner.fullname')}: N/A"
            )
        else:
            return (
                f"{Res.get('payment.account')}: {self.account_id}\n"
                f"{Res.get('payment.account.owner.fullname')}: {self.account_owner}"
            )

    def get_age_witness_input_data(self) -> bytes:
        return self.get_age_witness_input_data_using_bytes(
            self.account_id.encode("utf-8")
        )
