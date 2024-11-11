from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
from bisq.core.common.crypto.hash import get_crc32_hash
from electrum_min.bitcoin import base_decode
from electrum_min.util import to_bytes


class MileAddressValidator(AddressValidator):

    def validate(self, address: str):
        try:
            address = to_bytes(address, 'ascii')
            decoded = base_decode(address, base=58)
        except Exception as e:
            return AddressValidationResult.invalid_address(str(e))
        
        if len(decoded) != 32 + 4:
            return AddressValidationResult.invalid_address("Invalid address")
        
        payload = decoded[0:-4]
        csum_found = decoded[-4:]
        
        crc = get_crc32_hash(payload)

        if crc & 0xff != csum_found[0] or (crc >> 8) & 0xff != csum_found[1] or (crc >> 16) & 0xff != csum_found[2] or (crc >> 24) & 0xff != csum_found[3]:
            return AddressValidationResult.invalid_address("Invalid address checksum")
        
        return AddressValidationResult.valid_address()


class Mile(Coin):

    def __init__(self):
        super().__init__(
            name="Mile",
            ticker_symbol="MILE",
            address_validator=MileAddressValidator(),
        )
