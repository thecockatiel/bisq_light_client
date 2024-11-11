from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_sub1x_address_regex = re.compile(r'^[Z][a-km-zA-HJ-NP-Z1-9]{24,33}$')

class SUB1XAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_sub1x_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class SUB1X(Coin):
    
    class SUB1XParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 80
            self.p2sh_header = 13
    
    def __init__(self):
        super().__init__(
            name="SUB1X",
            ticker_symbol="SUB1X",
            address_validator=SUB1XAddressValidator(self.SUB1XParams()),
        )
