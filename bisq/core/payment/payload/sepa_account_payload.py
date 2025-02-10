from typing import TYPE_CHECKING, Optional
from bisq.core.locale.country_util import get_name_by_code
from bisq.core.locale.res import Res
from bisq.core.payment.payload.country_based_payment_account_payload import (
    CountryBasedPaymentAccountPayload,
)
from bisq.core.payment.payload.payload_with_holder_name import PayloadWithHolderName
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.locale.country import Country


class SepaAccountPayload(CountryBasedPaymentAccountPayload, PayloadWithHolderName):

    def __init__(
        self,
        payment_method_name: str,
        id: str,
        country_code: str = "",
        holder_name: str = "",
        iban: str = "",
        bic: str = "",
        email: str = "",
        accepted_country_codes: list[str] = None,
        accepted_countries: list["Country"] = None,
        max_trade_period: int = -1,
        exclude_from_json_data_map: Optional[dict[str, str]] = None,
    ):
        if accepted_country_codes is None and accepted_countries is None:
            raise ValueError(
                "Either accepted_country_codes or accepted_countries must be set"
            )
        if accepted_countries is not None:
            accepted_country_codes = sorted(
                list(set(country.code for country in accepted_countries))
            )
        super().__init__(
            payment_method_name,
            id,
            country_code,
            max_trade_period,
            exclude_from_json_data_map,
        )
        self._holder_name = holder_name
        self.iban = iban
        self.bic = bic
        self.email = email  # not used anymore but need to keep it for backward compatibility, must not be null but empty string, otherwise hash check fails for contract

        # Don't use a set here as we need a deterministic ordering, otherwise the contract hash does not match
        self.accepted_country_codes = accepted_country_codes
        self.persisted_accepted_country_codes: list[str] = accepted_country_codes.copy()

    @property
    def holder_name(self):
        return self._holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        self._holder_name = value

    def to_proto_message(self) -> protobuf.PaymentAccountPayload:
        sepa_payload = protobuf.SepaAccountPayload(
            holder_name=self.holder_name,
            iban=self.iban,
            bic=self.bic,
            email=self.email,
            accepted_country_codes=self.accepted_country_codes,
        )

        country_based_payload = (
            self.get_payment_account_payload_builder().country_based_payment_account_payload
        )
        country_based_payload.sepa_account_payload.CopyFrom(sepa_payload)

        payload = self.get_payment_account_payload_builder()
        payload.country_based_payment_account_payload.CopyFrom(country_based_payload)

        return payload

    @staticmethod
    def from_proto(proto: protobuf.PaymentAccountPayload) -> "SepaAccountPayload":
        country_based_payload = proto.country_based_payment_account_payload
        sepa_payload = country_based_payload.sepa_account_payload

        return SepaAccountPayload(
            payment_method_name=proto.payment_method_id,
            id=proto.id,
            country_code=country_based_payload.countryCode,
            holder_name=sepa_payload.holder_name,
            iban=sepa_payload.iban,
            bic=sepa_payload.bic,
            email=sepa_payload.email,
            accepted_country_codes=list(sepa_payload.accepted_country_codes),
            max_trade_period=proto.max_trade_period,
            exclude_from_json_data_map=dict(proto.exclude_from_json_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_accepted_country(self, country_code: str) -> None:
        if country_code not in self.accepted_country_codes:
            self.accepted_country_codes.append(country_code)

    def remove_accepted_country(self, country_code: str) -> None:
        if country_code in self.accepted_country_codes:
            self.accepted_country_codes.remove(country_code)

    def on_persist_changes(self) -> None:
        self.persisted_accepted_country_codes.clear()
        self.persisted_accepted_country_codes.extend(self.accepted_country_codes)

    def revert_changes(self) -> None:
        self.accepted_country_codes.clear()
        self.accepted_country_codes.extend(self.persisted_accepted_country_codes)

    def get_payment_details(self) -> str:
        method = Res.get(self.payment_method_id)
        owner = Res.get_with_col("payment.account.owner")
        country = Res.get_with_col("payment.bank.country")
        return (
            f"{method} - {owner}: {self.holder_name}, "
            f"IBAN: {self.iban}, BIC: {self.bic}, "
            f"{country}: {self.country_code}"
        )

    def get_payment_details_for_trade_popup(self) -> str:
        owner = Res.get_with_col("payment.account.owner")
        country = Res.get_with_col("payment.bank.country")
        return (
            f"{owner}: {self.holder_name}\n"
            f"IBAN: {self.iban}\n"
            f"BIC: {self.bic}\n"
            f"{country}: {get_name_by_code(self.country_code)}"
        )

    def get_age_witness_input_data(self) -> bytes:
        # We don't add holder_name because we don't want to break age validation if the user recreates an account with
        # slight changes in holder name (e.g. add or remove middle name)
        witness_bytes = self.iban.encode("utf-8") + self.bic.encode("utf-8")
        return self.get_age_witness_input_data_using_bytes(witness_bytes)

    @property
    def owner_id(self) -> str:
        return self.holder_name
