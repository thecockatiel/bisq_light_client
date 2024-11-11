from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
import re

_qbase_address_regex = re.compile(r'^[B][a-km-zA-HJ-NP-Z1-9]{25,34}$')

class QbaseAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if not re.match(_qbase_address_regex, address):
            return AddressValidationResult.invalid_structure()
        return super().validate(address)
    

class Qbase(Coin):
    
    class QbaseParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 25
            self.p2sh_header = 5
    
    def __init__(self):
        super().__init__(
            name="Qbase",
            ticker_symbol="QBS",
            address_validator=QbaseAddressValidator(self.QbaseParams()),
        )
