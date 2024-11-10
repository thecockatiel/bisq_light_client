
from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bitcoinj.core.network_parameters import NetworkParameters
from electrum_min.bitcoin import is_address as is_bitcoin_address
from electrum_min.constants import AbstractNet

class BitcoinAddressValidator(AddressValidator):
    
    def __init__(self, net: AbstractNet = None):
        super().__init__()
        self.network_parameters = net

    def validate(self, address: str):
        try: 
            result = is_bitcoin_address(address, net=self.network_parameters)
            if result:
                return AddressValidationResult.valid_address()
            else:
                return AddressValidationResult.invalid_address("Address is not a valid Base58 address.")
        except Exception as e:
            return AddressValidationResult.invalid_address(e)

