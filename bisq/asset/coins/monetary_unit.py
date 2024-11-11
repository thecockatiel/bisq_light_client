from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_monetary_unit_address_regex = re.compile(r'^[7][a-km-zA-HJ-NP-Z1-9]{24,33}$')

class MonetaryUnitAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_monetary_unit_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class MonetaryUnit(Coin):
    
    class MonetaryUnitParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 16
            self.p2sh_header = 76
    
    def __init__(self):
        super().__init__(
            name="MonetaryUnit",
            ticker_symbol="MUE",
            address_validator=MonetaryUnitAddressValidator(self.MonetaryUnitParams()),
        )
