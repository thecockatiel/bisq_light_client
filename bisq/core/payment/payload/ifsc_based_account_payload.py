from typing import TYPE_CHECKING, Union
from bisq.core.locale.bank_util import BankUtil
from bisq.core.locale.country_util import get_name_by_code
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.locale.country import Country


class IfscBasedAccountPayload(CountryBasedPaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str,
        holder_name: str = "",
        account_nr: str = "",
        ifsc: str = "",
        max_trade_period: int = -1,
        exclude_from_json_data_map: Union[dict[str, str]] = None,
    ):
        super().__init__(
            payment_method_name,
            id,
            country_code,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self.holder_name = holder_name
        self.account_nr = account_nr
        self.ifsc = ifsc

    def get_payment_account_payload_builder(self):
        builder = protobuf.IfscBasedAccountPayload(
            holder_name=self.holder_name,
        )
        if self.ifsc:
            builder.ifsc = self.ifsc
        if self.account_nr:
            builder.account_nr = self.account_nr
        country_based_payload = super().get_payment_account_payload_builder()
        country_based_payload.country_based_payment_account_payload.ifsc_based_account_payload.CopyFrom(
            builder
        )
        return country_based_payload

    def get_payment_details(self) -> str:
        return (
            "Ifsc account transfer - "
            + self.get_payment_details_for_trade_popup().replace("\n", ", ")
        )

    def get_payment_details_for_trade_popup(self) -> str:
        owner_label = Res.get_with_col("payment.account.owner")
        account_nr_label = BankUtil.get_account_nr_label(self.country_code)
        bank_id_label = BankUtil.get_bank_id_label(self.country_code)
        country_name = get_name_by_code(self.country_code)
        bank_country_label = Res.get_with_col("payment.bank.country")
        return (
            f"{owner_label} {self.holder_name}\n"
            f"{account_nr_label}: {self.account_nr}\n"
            f"{bank_id_label}: {self.ifsc}\n"
            f"{bank_country_label} {country_name}"
        )

    def get_age_witness_input_data(self) -> bytes:
        # We don't add holder_name because we don't want to break age validation if the user recreates an account with
        # slight changes in holder name (e.g. add or remove middle name)
        witness_bytes = (self.account_nr + self.ifsc).encode("utf-8")
        return self.get_age_witness_input_data_using_bytes(witness_bytes)

    @property
    def owner_id(self) -> str:
        return self.holder_name
