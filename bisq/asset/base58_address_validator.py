from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bitcoinj.core.network_parameters import MainNetParams, NetworkParameters
from electrum_min.bitcoin import b58_address_to_hash160

# a slightly modified version of electrum's, to work with NetworkParameters:
def is_b58_address_compat(addr: str, network_params: NetworkParameters) -> bool:
    if network_parameters is None: network_parameters = MainNetParams()
    try:
        # test length, checksum, encoding:
        addrtype, h = b58_address_to_hash160(addr)
    except Exception as e:
        return False
    if addrtype not in [network_params.address_header, network_params.p2sh_header]:
        return False
    return True

class Base58AddressValidator(AddressValidator):
    
    def __init__(self, network_parameters: NetworkParameters = None):
        super().__init__()
        self.network_parameters = network_parameters

    def validate(self, address: str):
        try: 
            result = is_b58_address_compat(address, self.network_parameters)
            if result:
                return AddressValidationResult.valid_address()
            else:
                return AddressValidationResult.invalid_address("Address is not a valid Base58 address.")
        except Exception as e:
            return AddressValidationResult.invalid_address(e)

