from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_pivx_address_regex = re.compile(r'^[D][a-km-zA-HJ-NP-Z1-9]{24,33}$')

class PIVXAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_pivx_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class PIVX(Coin):
    
    class PIVXParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 30
            self.p2sh_header = 13
    
    def __init__(self):
        super().__init__(
            name="PIVX",
            ticker_symbol="PIVX",
            address_validator=PIVXAddressValidator(self.PIVXParams()),
        )
