from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_ucc_address_regex = re.compile(r'^[U][a-km-zA-HJ-NP-Z1-9]{33}$')

class UnitedCommunityCoinAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_ucc_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class UnitedCommunityCoin(Coin):
    
    class UnitedCommunityCoinParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 68
            self.p2sh_header = 18
    
    def __init__(self):
        super().__init__(
            name="UnitedCommunityCoin",
            ticker_symbol="UCC",
            address_validator=UnitedCommunityCoinAddressValidator(self.UnitedCommunityCoinParams()),
        )
