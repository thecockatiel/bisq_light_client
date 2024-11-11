from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.base58_address_validator import Base58AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter

# NOTE: this validator is same as java bisq

class ZeroAddressValidator():
    
    def validate(self, address: str):
        #  We only support t addresses (transparent transactions)
        if not address.startswith("t1"):
            return AddressValidationResult.invalid_address("", "validation.altcoin.zAddressesNotSupported")
        
        return AddressValidationResult.valid_address()
    

class Zero(Coin):

    def __init__(self):
        super().__init__(
            name="Zero",
            ticker_symbol="ZER",
            address_validator=ZeroAddressValidator(),
        )
