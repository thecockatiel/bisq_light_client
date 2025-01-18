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
        if country_code == "BR":
            return Res.get("payment.bank.name")
        else:
            return Res.get("payment.bank.name") if BankUtil.is_bank_name_required(country_code) else Res.get("payment.bank.nameOptional")

    @staticmethod
    def is_bank_id_required(country_code: str) -> bool:
        if country_code in ["GB", "US", "BR", "NZ", "AU", "SE", "CL", "NO", "AR"]:
            return False
        elif country_code in ["CA", "MX", "HK"]:
            return True
        else:
            return True

    @staticmethod
    def get_bank_id_label(country_code: str) -> str:
        if country_code == "CA":
            return "Institution Number" # do not translate as it is used in English only
        elif country_code in ["MX", "HK"]:
            return Res.get("payment.bankCode")
        else:
            return Res.get("payment.bankId") if BankUtil.is_bank_id_required(country_code) else Res.get("payment.bankIdOptional")

    @staticmethod
    def is_branch_id_required(country_code: str) -> bool:
        if country_code in ["GB", "US", "BR", "AU", "CA"]:
            return True
        elif country_code in ["NZ", "MX", "HK", "SE", "NO"]:
            return False
        else:
            return True

    @staticmethod
    def get_branch_id_label(country_code: str) -> str:
        if country_code == "GB":
            return "UK sort code" # do not translate as it is used in English only
        elif country_code == "US":
            return "Routing Number" # do not translate as it is used in English only
        elif country_code == "BR":
            return "Código da Agência" # do not translate as it is used in Portuguese only
        elif country_code == "AU":
            return "BSB code" # do not translate as it is used in English only
        elif country_code == "CA":
            return "Transit Number" # do not translate as it is used in English only
        else:
            return Res.get("payment.branchNr") if BankUtil.is_branch_id_required(country_code) else Res.get("payment.branchNrOptional")

    @staticmethod
    def is_account_nr_required(country_code: str) -> bool:
        return True

    @staticmethod
    def get_account_nr_label(country_code: str) -> str:
        if country_code in ["GB", "US", "BR", "NZ", "AU", "CA", "HK"]:
            return Res.get("payment.accountNr")
        elif country_code in ["NO", "SE"]:
            return "Kontonummer" # do not translate as it is used in Norwegian and Swedish only
        elif country_code == "MX":
            return "CLABE" # do not translate as it is used in Spanish only
        elif country_code == "CL":
            return "Cuenta" # do not translate as it is used in Spanish only
        elif country_code == "AR":
            return "Número de cuenta" # do not translate as it is used in Spanish only
        else:
            return Res.get("payment.accountNrLabel")

    @staticmethod
    def is_account_type_required(country_code: str) -> bool:
        if country_code in ["US", "BR", "CA"]:
            return True
        else:
            return False

    @staticmethod
    def get_account_type_label(country_code: str) -> str:
        if country_code in ["US", "BR", "CA"]:
            return Res.get("payment.accountType")
        else:
            return ""

    @staticmethod
    def get_account_type_values(country_code: str) -> List[str]:
        if country_code in ["US", "BR", "CA"]:
            return [Res.get("payment.checking"), Res.get("payment.savings")]
        else:
            return []

    @staticmethod
    def is_holder_id_required(country_code: str) -> bool:
        if country_code in ["BR", "CL", "AR"]:
            return True
        else:
            return False

    @staticmethod
    def get_holder_id_label(country_code: str) -> str:
        if country_code == "BR":
            return "Cadastro de Pessoas Físicas (CPF)" # do not translate as it is used in Portuguese only
        elif country_code == "CL":
            return "Rol Único Tributario (RUT)" # do not translate as it is used in Spanish only
        elif country_code == "AR":
            return "CUIL/CUIT" # do not translate as it is used in Spanish only
        else:
            return Res.get("payment.personalId")

    @staticmethod
    def get_holder_id_label_short(country_code: str) -> str:
        if country_code == "BR":
            return "CPF" # do not translate as it is used in portuguese only
        elif country_code == "CL":
            return "RUT" # do not translate as it is used in spanish only
        elif country_code == "AR":
            return "CUIT"
        else:
            return "ID"

    @staticmethod
    def use_validation(country_code: str) -> bool:
        if country_code in ["GB", "US", "BR", "AU", "CA", "NZ", "MX", "HK", "SE", "NO", "AR"]:
            return True
        else:
            return False

    @staticmethod
    def is_state_required(country_code: str) -> bool:
        if country_code in ["US", "CA", "AU", "MY", "MX", "CN"]:
            return True
        else:
            return False

    @staticmethod
    def is_national_account_id_required(country_code: str) -> bool:
        if country_code == "AR":
            return True
        else:
            return False

    @staticmethod
    def get_national_account_id_label(country_code: str) -> str:
        if country_code == "AR":
            return Res.get("payment.national.account.id.AR")
        else:
            return ""
