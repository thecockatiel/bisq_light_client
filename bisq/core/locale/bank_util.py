from bisq.core.locale.res import Res
from typing import List

class BankUtil:
    @staticmethod
    def is_bank_name_required(country_code: str) -> bool:
        # Currently we always return true but let's keep that method to be more flexible in case we want to not show
        # it at some new payment method.
        return True

    @staticmethod
    def get_bank_name_label(country_code: str) -> str:
        match country_code:
            case "BR":
                return Res.get("payment.bank.name")
            case _:
                return Res.get("payment.bank.name") if BankUtil.is_bank_name_required(country_code) else Res.get("payment.bank.nameOptional")

    @staticmethod
    def is_bank_id_required(country_code: str) -> bool:
        match country_code:
            case "GB" | "US" | "BR" | "NZ" | "AU" | "SE" | "CL" | "NO" | "AR":
                return False
            case "CA" | "MX" | "HK":
                return True
            case _:
                return True

    @staticmethod
    def get_bank_id_label(country_code: str) -> str:
        match country_code:
            case "CA":
                return "Institution Number" # do not translate as it is used in English only
            case "MX" | "HK":
                return Res.get("payment.bankCode")
            case _:
                return Res.get("payment.bankId") if BankUtil.is_bank_id_required(country_code) else Res.get("payment.bankIdOptional")

    @staticmethod
    def is_branch_id_required(country_code: str) -> bool:
        match country_code:
            case "GB" | "US" | "BR" | "AU" | "CA":
                return True
            case "NZ" | "MX" | "HK" | "SE" | "NO":
                return False
            case _:
                return True

    @staticmethod
    def get_branch_id_label(country_code: str) -> str:
        match country_code:
            case "GB":
                return "UK sort code" # do not translate as it is used in English only
            case "US":
                return "Routing Number" # do not translate as it is used in English only
            case "BR":
                return "Código da Agência" # do not translate as it is used in Portuguese only
            case "AU":
                return "BSB code" # do not translate as it is used in English only
            case "CA":
                return "Transit Number" # do not translate as it is used in English only
            case _:
                return Res.get("payment.branchNr") if BankUtil.is_branch_id_required(country_code) else Res.get("payment.branchNrOptional")

    @staticmethod
    def is_account_nr_required(country_code: str) -> bool:
        return True

    @staticmethod
    def get_account_nr_label(country_code: str) -> str:
        match country_code:
            case "GB" | "US" | "BR" | "NZ" | "AU" | "CA" | "HK":
                return Res.get("payment.accountNr")
            case "NO" | "SE":
                return "Kontonummer" # do not translate as it is used in Norwegian and Swedish only
            case "MX":
                return "CLABE" # do not translate as it is used in Spanish only
            case "CL":
                return "Cuenta" # do not translate as it is used in Spanish only
            case "AR":
                return "Número de cuenta" # do not translate as it is used in Spanish only
            case _:
                return Res.get("payment.accountNrLabel")

    @staticmethod
    def is_account_type_required(country_code: str) -> bool:
        match country_code:
            case "US" | "BR" | "CA":
                return True
            case _:
                return False

    @staticmethod
    def get_account_type_label(country_code: str) -> str:
        match country_code:
            case "US" | "BR" | "CA":
                return Res.get("payment.accountType")
            case _:
                return ""

    @staticmethod
    def get_account_type_values(country_code: str) -> List[str]:
        match country_code:
            case "US" | "BR" | "CA":
                return [Res.get("payment.checking"), Res.get("payment.savings")]
            case _:
                return []

    @staticmethod
    def is_holder_id_required(country_code: str) -> bool:
        match country_code:
            case "BR" | "CL" | "AR":
                return True
            case _:
                return False

    @staticmethod
    def get_holder_id_label(country_code: str) -> str:
        match country_code:
            case "BR":
                return "Cadastro de Pessoas Físicas (CPF)" # do not translate as it is used in Portuguese only
            case "CL":
                return "Rol Único Tributario (RUT)" # do not translate as it is used in Spanish only
            case "AR":
                return "CUIL/CUIT" # do not translate as it is used in Spanish only
            case _:
                return Res.get("payment.personalId")

    @staticmethod
    def get_holder_id_label_short(country_code: str) -> str:
        match country_code:
            case "BR":
                return "CPF" # do not translate as it is used in portuguese only
            case "CL":
                return "RUT" # do not translate as it is used in spanish only
            case "AR":
                return "CUIT"
            case _:
                return "ID"

    @staticmethod
    def use_validation(country_code: str) -> bool:
        match country_code:
            case "GB" | "US" | "BR" | "AU" | "CA" | "NZ" | "MX" | "HK" | "SE" | "NO" | "AR":
                return True
            case _:
                return False

    @staticmethod
    def is_state_required(country_code: str) -> bool:
        match country_code:
            case "US" | "CA" | "AU" | "MY" | "MX" | "CN":
                return True
            case _:
                return False

    @staticmethod
    def is_national_account_id_required(country_code: str) -> bool:
        match country_code:
            case "AR":
                return True
            case _:
                return False

    @staticmethod
    def get_national_account_id_label(country_code: str) -> str:
        match country_code:
            case "AR":
                return Res.get("payment.national.account.id.AR")
            case _:
                return ""
