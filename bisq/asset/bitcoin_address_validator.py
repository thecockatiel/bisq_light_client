
from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bisq.asset.base58_address_validator import is_b58_address_compat
from bitcoinj.core.network_parameters import MainNetParams, NetworkParameters
from electrum_min import segwit_addr

def is_segwit_address_compat(addr: str, network_parameters: NetworkParameters=None) -> bool:
    if network_parameters is None: network_parameters = MainNetParams()
    try:
        witver, witprog = segwit_addr.decode_segwit_address(network_parameters.segwit_address_hrp, addr)
    except Exception as e:
        return False
    return witprog is not None

class BitcoinAddressValidator(AddressValidator):
    
    def __init__(self, network_parameters: NetworkParameters = None):
        super().__init__()
        self.network_parameters = network_parameters

    def validate(self, address: str):
        try: 
            result = is_segwit_address_compat(address, self.network_parameters) or is_b58_address_compat(address, self.network_parameters)
            if result:
                return AddressValidationResult.valid_address()
            else:
                return AddressValidationResult.invalid_address("Address is not a valid bitcoin address.")
        except Exception as e:
            return AddressValidationResult.invalid_address(e)

