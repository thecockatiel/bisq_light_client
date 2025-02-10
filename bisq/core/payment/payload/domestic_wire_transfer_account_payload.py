from bisq.core.locale.bank_util import BankUtil
from bisq.core.locale.res import Res
from bisq.core.payment.payload.bank_account_payload import BankAccountPayload
import pb_pb2 as protobuf
from typing import Dict, Optional


class DomesticWireTransferAccountPayload(BankAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: Optional[str] = None,
        holder_name: Optional[str] = None,
        bank_name: Optional[str] = None,
        branch_id: Optional[str] = None,
        account_nr: Optional[str] = None,
        holder_address: Optional[str] = None,
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
            None,  # account_type not used
            None,  # holder_tax_id not used
            None,  # bank_id not used
            None,  # national_account_id not used
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.holder_address = holder_address

    def to_proto_message(self):
        domestic_wire = protobuf.DomesticWireTransferAccountPayload(
            holder_address=self.holder_address
        )

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.bank_account_payload.domestic_wire_transfer_account_payload.CopyFrom(
            domestic_wire
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        country_based = proto.country_based_payment_account_payload
        bank_account = country_based.bank_account_payload
        domestic_wire_payload = bank_account.domestic_wire_transfer_account_payload

        return DomesticWireTransferAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based.countryCode,  # Weird protobuf names
            holder_name=bank_account.holder_name,
            bank_name=bank_account.bank_name or None,
            branch_id=bank_account.branch_id or None,
            account_nr=bank_account.account_nr or None,
            holder_address=domestic_wire_payload.holder_address or None,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    def get_payment_details(self):
        payment_method = Res.get(self.payment_method_id)
        account_owner = Res.get_with_col("payment.account.owner")
        bank_name_label = BankUtil.get_bank_name_label(self.country_code)
        branch_id_label = BankUtil.get_branch_id_label(self.country_code)
        account_nr_label = BankUtil.get_account_nr_label(self.country_code)

        payment_details = (
            f"{payment_method} - {account_owner} {self.holder_name}, "
            f"{bank_name_label}: {self.bank_name}, "
            f"{branch_id_label}: {self.branch_id}, "
            f"{account_nr_label}: {self.account_nr}"
        )
        return payment_details
