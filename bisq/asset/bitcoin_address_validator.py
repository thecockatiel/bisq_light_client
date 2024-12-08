
from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bitcoinj.core.address import Address
from bitcoinj.core.network_parameters import NetworkParameters

class BitcoinAddressValidator(AddressValidator):
    
    def __init__(self, network_parameters: NetworkParameters = None):
        super().__init__()
        self.network_parameters = network_parameters

    def validate(self, address: str):
        try: 
            result = Address.is_segwit_address(address, self.network_parameters) or Address.is_b58_address(address, self.network_parameters)
            if result:
                return AddressValidationResult.valid_address()
            else:
                return AddressValidationResult.invalid_address("Address is not a valid bitcoin address.")
        except Exception as e:
            return AddressValidationResult.invalid_address(e)

