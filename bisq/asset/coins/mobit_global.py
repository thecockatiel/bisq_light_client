from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_mobit_global_address_regex = re.compile(r'^[M][a-zA-Z1-9]{33}$')

class AdeptioAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_mobit_global_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class MobitGlobal(Coin):
    
    class MobitGlobalParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 50
            self.p2sh_header = 110
    
    def __init__(self):
        super().__init__(
            name="MobitGlobal",
            ticker_symbol="MBGL",
            address_validator=AdeptioAddressValidator(self.MobitGlobalParams()),
        )
