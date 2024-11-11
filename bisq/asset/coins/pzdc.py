from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_pzdc_address_regex = re.compile(r'^[P][a-km-zA-HJ-NP-Z1-9]{24,33}$')

class PZDCAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_pzdc_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class PZDC(Coin):
    
    class PZDCParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 55
            self.p2sh_header = 13
    
    def __init__(self):
        super().__init__(
            name="PZDC",
            ticker_symbol="PZDC",
            address_validator=PZDCAddressValidator(self.PZDCParams()),
        )
