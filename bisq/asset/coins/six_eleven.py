from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_six_eleven_address_regex = re.compile(r'^[MN][123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{33}$')

class SixElevenAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_six_eleven_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class SixEleven(Coin):
    
    class SixElevenParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 52
            self.p2sh_header = None
    
    def __init__(self):
        super().__init__(
            name="SixEleven",
            ticker_symbol="SIL",
            address_validator=SixElevenAddressValidator(self.SixElevenParams()),
        )
