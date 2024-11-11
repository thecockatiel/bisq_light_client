from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter

class GenesisAddressValidator(Base58AddressValidator):
    def __init__(self, network_parameters: NetworkParametersAdapter):
        super().__init__(network_parameters)
    
    def validate(self, address: str):
        if address.startswith("S"):
            return super().validate(address)
        elif address.startswith("genx"):
            return AddressValidationResult.invalid_address("Bech32 GENX addresses are not supported on bisq")
        elif address.startswith("C"):
            return AddressValidationResult.invalid_address("Legacy GENX addresses are not supported on bisq")
        else:
            return AddressValidationResult.invalid_structure()
    

class Genesis(Coin):
    
    class GenesisParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 28
            self.p2sh_header = 63
    
    def __init__(self):
        super().__init__(
            name="Genesis",
            ticker_symbol="GENX",
            address_validator=GenesisAddressValidator(self.GenesisParams()),
        )
