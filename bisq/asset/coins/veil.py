from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter

class VeilAddressValidator(Base58AddressValidator):
    
    def validate(self, address: str):
        if address.startswith("V"):
            return super().validate(address)
        elif address.startswith("bv"):
            # TODO: Add bech32 support (note in java bisq)
            return AddressValidationResult.invalid_address("Bech32 addresses not supported on bisq")
        else:
            return AddressValidationResult.invalid_structure()
    

class Veil(Coin):
    
    class VeilParams(NetworkParametersAdapter):
        def __init__(self):
            super().__init__()
            self.address_header = 70
            self.p2sh_header = 5
    
    def __init__(self):
        super().__init__(
            name="Veil",
            ticker_symbol="VEIL",
            address_validator=VeilAddressValidator(self.VeilParams()),
        )
