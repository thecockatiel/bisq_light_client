from bisq.core.locale.res import Res
from bisq.core.payment.payload.bank_account_payload import BankAccountPayload
import pb_pb2 as protobuf
from typing import Dict


class NationalBankAccountPayload(BankAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = None,
        holder_name: str = None,
        bank_name: str = None,
        branch_id: str = None,
        account_nr: str = None,
        account_type: str = None,
        holder_tax_id: str = None,
        bank_id: str = None,
        national_account_id: str = None,
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
            holder_tax_id,
            bank_id,
            national_account_id,
            max_trade_period,
            exclude_from_json_data_map,
        )

    def to_proto_message(self):
        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.bank_account_payload.national_bank_account_payload.CopyFrom(
            protobuf.NationalBankAccountPayload()
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        country_based = proto.country_based_payment_account_payload
        bank_account = country_based.bank_account_payload

        return NationalBankAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based.countryCode,  # Weird protobuf names
            holder_name=bank_account.holder_name,
            bank_name=bank_account.bank_name or None,
            branch_id=bank_account.branch_id or None,
            account_nr=bank_account.account_nr or None,
            account_type=bank_account.account_type or None,
            holder_tax_id=bank_account.holder_tax_id or None,
            bank_id=bank_account.bank_id or None,
            national_account_id=bank_account.national_account_id or None,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        details = self.get_payment_details_for_trade_popup().replace("\n", ", ")
        return f"{Res.get(self.payment_method_id)} - {details}"
