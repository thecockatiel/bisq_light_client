from bisq.core.locale.bank_util import BankUtil
from bisq.core.locale.country_util import get_name_by_code
from bisq.core.locale.res import Res
from bisq.core.payment.payload.bank_account_payload import BankAccountPayload
import pb_pb2 as protobuf
from typing import Dict, Optional


class CashDepositAccountPayload(BankAccountPayload):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: str = "",
        holder_email: Optional[str] = None,
        bank_name: Optional[str] = "",
        branch_id: Optional[str] = "",
        account_nr: Optional[str] = "",
        account_type: Optional[str] = None,
        requirements: Optional[str] = None,
        holder_tax_id: Optional[str] = None,
        bank_id: Optional[str] = "",
        national_account_id: Optional[str] = None,
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
        self.holder_email = holder_email
        self.requirements = requirements

    def to_proto_message(self):
        deposit_payload = protobuf.CashDepositAccountPayload(
            holder_name=self.holder_name,
        )
        if self.holder_email:
            deposit_payload.holder_email = self.holder_email
        if self.bank_name:
            deposit_payload.bank_name = self.bank_name
        if self.branch_id:
            deposit_payload.branch_id = self.branch_id
        if self.account_nr:
            deposit_payload.account_nr = self.account_nr
        if self.account_type:
            deposit_payload.account_type = self.account_type
        if self.requirements:
            deposit_payload.requirements = self.requirements
        if self.holder_tax_id:
            deposit_payload.holder_tax_id = self.holder_tax_id
        if self.bank_id:
            deposit_payload.bank_id = self.bank_id
        if self.national_account_id:
            deposit_payload.national_account_id = self.national_account_id

        builder = self.get_payment_account_payload_builder()
        builder.country_based_payment_account_payload.cash_deposit_account_payload.CopyFrom(
            deposit_payload
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload):
        country_based = proto.country_based_payment_account_payload
        deposit_payload = country_based.cash_deposit_account_payload

        return CashDepositAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based.countryCode,  # Weird protobuf names
            holder_name=deposit_payload.holder_name,
            holder_email=deposit_payload.holder_email or None,
            bank_name=deposit_payload.bank_name or None,
            branch_id=deposit_payload.branch_id or None,
            account_nr=deposit_payload.account_nr or None,
            account_type=deposit_payload.account_type or None,
            requirements=deposit_payload.requirements or None,
            holder_tax_id=deposit_payload.holder_tax_id or None,
            bank_id=deposit_payload.bank_id or None,
            national_account_id=deposit_payload.national_account_id or None,
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    def get_payment_details(self) -> str:
        details = self.get_payment_details_for_trade_popup().replace("\n", ", ")
        return f"Cash deposit - {details}"

    def get_payment_details_for_trade_popup(self):
        bank_name = (
            f"{BankUtil.get_bank_name_label(self.country_code)}: {self.bank_name}\n"
            if BankUtil.is_bank_name_required(self.country_code)
            else ""
        )
        bank_id = (
            f"{BankUtil.get_bank_id_label(self.country_code)}: {self.bank_id}\n"
            if BankUtil.is_bank_id_required(self.country_code)
            else ""
        )
        branch_id = (
            f"{BankUtil.get_branch_id_label(self.country_code)}: {self.branch_id}\n"
            if BankUtil.is_branch_id_required(self.country_code)
            else ""
        )
        national_account_id = (
            f"{BankUtil.get_national_account_id_label(self.country_code)}: {self.national_account_id}\n"
            if BankUtil.is_national_account_id_required(self.country_code)
            else ""
        )
        account_nr = (
            f"{BankUtil.get_account_nr_label(self.country_code)}: {self.account_nr}\n"
            if BankUtil.is_account_nr_required(self.country_code)
            else ""
        )
        account_type = (
            f"{BankUtil.get_account_type_label(self.country_code)}: {self.account_type}\n"
            if BankUtil.is_account_type_required(self.country_code)
            else ""
        )
        holder_tax_id_string = (
            f"{BankUtil.get_holder_id_label(self.country_code)}: {self.holder_tax_id}\n"
            if BankUtil.is_holder_id_required(self.country_code)
            else ""
        )
        requirements_string = (
            f"{Res.get_with_col('payment.extras')} {self.requirements}\n"
            if self.requirements
            else ""
        )
        email_string = (
            f"{Res.get_with_col('payment.email')} {self.holder_email}\n"
            if self.holder_email
            else ""
        )

        return (
            f"{Res.get_with_col('payment.account.owner')} {self.holder_name}\n"
            f"{email_string}"
            f"{bank_name}"
            f"{bank_id}"
            f"{branch_id}"
            f"{national_account_id}"
            f"{account_nr}"
            f"{account_type}"
            f"{holder_tax_id_string}"
            f"{requirements_string}"
            f"{Res.get_with_col('payment.bank.country')} {get_name_by_code(self.country_code)}"
        )
