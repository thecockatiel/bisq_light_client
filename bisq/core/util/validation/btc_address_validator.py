from bisq.core.locale.res import Res
from bisq.core.util.validation.input_validation_result import InputValidationResult
from bisq.core.util.validation.input_validator import InputValidator
from bitcoinj.core.address import Address
from bitcoinj.core.address_format_exception import AddressFormatException

class BtcAddressValidator(InputValidator):
    
    def validate(self, input_str: str):
        result = self.validate_if_not_empty(input_str)
        if result.is_valid:
            return self.validate_btc_address(input_str)
        else:
            return result
        
    def validate_btc_address(self, input_str: str):
        if self.allow_empty and (input_str is None or input_str.strip() == ""):
            return InputValidationResult(True)
        from global_container import GLOBAL_CONTAINER
        try:
            Address.from_string(input_str, GLOBAL_CONTAINER.value.config.base_currency_network_parameters)
            return InputValidationResult(True)
        except AddressFormatException:
            return InputValidationResult(False, Res.get("validation.btc.invalidFormat"))
