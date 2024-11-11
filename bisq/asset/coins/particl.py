from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_particl_address_regex = re.compile(r'^[RP][a-km-zA-HJ-NP-Z1-9]{25,34}$')

class ParticlAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_particl_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class Particl(Coin):
    
    class ParticlParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 56
            self.p2sh_header = 60
    
    def __init__(self):
        super().__init__(
            name="Particl",
            ticker_symbol="PART",
            address_validator=ParticlAddressValidator(self.ParticlParams()),
        )
