from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.bank_account_payload import BankAccountPayload
import pb_pb2 as protobuf
from typing import Dict, Optional


class AchTransferAccountPayload(BankAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: str = "",
        bank_name: Optional[str] = "",
        branch_id: Optional[str] = "",
        account_nr: Optional[str] = "",
        account_type: Optional[str] = None,
        holder_address: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Dict[str, str] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            country_code,
            holder_name,
            bank_name,
            branch_id,
            account_nr,
            account_type,
            None,  # holder_tax_id not used
            None,  # bank_id not used
            None,  # national_account_id not used
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.holder_address = holder_address

    def to_proto_message(self):
        ach_transfer = protobuf.AchTransferAccountPayload(
            holder_address=self.holder_address
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.bank_account_payload.ach_transfer_account_payload.CopyFrom(
            ach_transfer
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        country_based = proto.country_based_payment_account_payload
        bank_account = country_based.bank_account_payload
        ach_payload = bank_account.ach_transfer_account_payload

        return AchTransferAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based.country_code,
            holder_name=bank_account.holder_name,
            bank_name=bank_account.bank_name or None,
            branch_id=bank_account.branch_id or None,
            account_nr=bank_account.account_nr or None,
            account_type=bank_account.account_type or None,
            holder_address=ach_payload.holder_address or None,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=ProtoUtil.to_string_map(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        return (
            Res.get(self.payment_method_id)
            + " - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )
