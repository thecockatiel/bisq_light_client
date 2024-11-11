import re
from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator


class RegexAddressValidator(AddressValidator):
    """
    Validates an Asset address against a given regular expression.
    """
    
    def __init__(self, regex: str, error_msg_i18n_key: str = None):
        super().__init__()
        self.regex = re.compile(regex)
        self.error_msg_i18n_key = error_msg_i18n_key

    def validate(self, address: str):
        if not re.match(self.regex, address):
            if self.error_msg_i18n_key:
                return AddressValidationResult.invalid_address("", self.error_msg_i18n_key)
            else:
                return AddressValidationResult.invalid_structure()
        return AddressValidationResult.valid_address()
