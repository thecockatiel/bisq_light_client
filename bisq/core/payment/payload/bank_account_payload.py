from typing import TYPE_CHECKING, Optional
from bisq.core.locale.bank_util import BankUtil
from bisq.core.locale.country_util import get_name_by_code
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
import pb_pb2 as protobuf


class BankAccountPayload(CountryBasedPaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: str = "",
        bank_name: Optional[str] = "",
        branch_id: Optional[str] = "",
        account_nr: Optional[str] = "",
        account_type: Optional[str] = "",
        holder_tx_id: Optional[str] = "",
        bank_id: Optional[str] = "",
        national_account_id: Optional[str] = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            country_code,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.holder_name = holder_name
        self.bank_name = bank_name
        self.branch_id = branch_id
        self.account_nr = account_nr
        self.account_type = account_type
        self.holder_tx_id = holder_tx_id
        self.bank_id = bank_id
        self.national_account_id = national_account_id

    def get_payment_account_payload_builder(self):
        builder = protobuf.BankAccountPayload(
            holder_name=self.holder_name,
        )

        if self.holder_tx_id:
            builder.holder_tax_id = self.holder_tx_id
        if self.bank_name:
            builder.bank_name = self.bank_name
        if self.branch_id:
            builder.branch_id = self.branch_id
        if self.account_nr:
            builder.account_nr = self.account_nr
        if self.account_type:
            builder.account_type = self.account_type
        if self.bank_id:
            builder.bank_id = self.bank_id
        if self.national_account_id:
            builder.national_account_id = self.national_account_id

        country_based_builder = (
            super()
            .get_payment_account_payload_builder()
            .country_based_payment_account_payload
        )
        country_based_builder.bank_account_payload.CopyFrom(builder)

        payment_account_payload = super().get_payment_account_payload_builder()
        payment_account_payload.country_based_payment_account_payload.CopyFrom(
            country_based_builder
        )

        return payment_account_payload

    def get_payment_details(self) -> str:
        return (
            "Bank account transfer - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )

    def get_payment_details_for_trade_popup(self) -> str:
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
            f"{BankUtil.get_holder_id_label(self.country_code)}: {self.holder_tx_id}\n"
            if BankUtil.is_holder_id_required(self.country_code)
            else ""
        )

        return (
            f"{Res.get_with_col('payment.account.owner')} {self.holder_name}\n"
            f"{bank_name}"
            f"{bank_id}"
            f"{branch_id}"
            f"{national_account_id}"
            f"{account_nr}"
            f"{account_type}"
            f"{holder_tax_id_string}"
            f"{Res.get_with_col('payment.bank.country')} {get_name_by_code(self.country_code)}"
        )

    def get_holder_id_label(self) -> str:
        return BankUtil.get_holder_id_label(self.country_code)

    def get_bank_id(self) -> Optional[str]:
        return (
            self.bank_id
            if BankUtil.is_bank_id_required(self.country_code)
            else self.bank_name
        )

    def get_age_witness_input_data(self) -> bytes:
        bank_name = (
            self.bank_name if BankUtil.is_bank_name_required(self.country_code) else ""
        )
        bank_id = (
            self.bank_id if BankUtil.is_bank_id_required(self.country_code) else ""
        )
        branch_id = (
            self.branch_id if BankUtil.is_branch_id_required(self.country_code) else ""
        )
        account_nr = (
            self.account_nr
            if BankUtil.is_account_nr_required(self.country_code)
            else ""
        )
        account_type = (
            self.account_type
            if BankUtil.is_account_type_required(self.country_code)
            else ""
        )
        holder_tax_id_string = (
            f"{BankUtil.get_holder_id_label(self.country_code)} {self.holder_tx_id}\n"
            if BankUtil.is_holder_id_required(self.country_code)
            else ""
        )
        national_account_id = (
            self.national_account_id
            if BankUtil.is_national_account_id_required(self.country_code)
            else ""
        )

        # We don't add holder_name because we don't want to break age validation if the user recreates an account with
        # slight changes in holder name (e.g. add or remove middle name)
        all_data = (
            f"{bank_name}"
            f"{bank_id}"
            f"{branch_id}"
            f"{account_nr}"
            f"{account_type}"
            f"{holder_tax_id_string}"
            f"{national_account_id}"
        )

        return self.get_age_witness_input_data_using_bytes(all_data.encode("utf-8"))

    @property
    def owner_id(self) -> str:
        return self.holder_name
