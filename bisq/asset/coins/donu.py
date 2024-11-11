from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_donu_address_regex = re.compile(r'^[N][a-km-zA-HJ-NP-Z1-9]{24,33}$')

class DonuAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_donu_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class Donu(Coin):
    
    class DonuParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 53
            self.p2sh_header = 5
    
    def __init__(self):
        super().__init__(
            name="Donu",
            ticker_symbol="DONU",
            address_validator=DonuAddressValidator(self.DonuParams()),
        )
