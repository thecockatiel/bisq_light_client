from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_ida_pay_address_regex = re.compile(r'^[CD][a-km-zA-HJ-NP-Z1-9]{33}$')

class IdaPayAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_ida_pay_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class IdaPay(Coin):
    
    class IdaPayParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 29
            self.p2sh_header = 36
    
    def __init__(self):
        super().__init__(
            name="IdaPay",
            ticker_symbol="IDA",
            address_validator=IdaPayAddressValidator(self.IdaPayParams()),
        )
