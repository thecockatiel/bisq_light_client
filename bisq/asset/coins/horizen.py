from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bisq.asset.coin import Coin
from electrum_min.bitcoin import DecodeBase58Check


class HorizenAddressValidator(AddressValidator):

    def validate(self, address: str):
        try:
            # Get the non Base58 form of the address and the bytecode of the first two bytes
            byte_address = DecodeBase58Check(address)
        except Exception as e:
            # Unhandled Exception (probably a checksum error)
            return AddressValidationResult.invalid_address(e)
        
        version0 = byte_address[0] & 0xFF
        version1 = byte_address[1] & 0xFF
        
        # We only support public ("zn" (0x20,0x89), "t1" (0x1C,0xB8))
        # and multisig ("zs" (0x20,0x96), "t3" (0x1C,0xBD)) addresses
        
        # Fail for private addresses
        if version0 == 0x16 and version1 == 0x9A:
            # Address starts with "zc"
            return AddressValidationResult.invalid_address("", "validation.altcoin.zAddressesNotSupported")
        
        if version0 == 0x1C and (version1 == 0xB8 or version1 == 0xBD):
            # "t1" or "t3" address
            return AddressValidationResult.valid_address()
        
        if version0 == 0x20 and (version1 == 0x89 or version1 == 0x96):
            # "zn" or "zs" address
            return AddressValidationResult.valid_address()
        
        # Unknown Type
        return AddressValidationResult.invalid_structure()


class Horizen(Coin):

    def __init__(self):
        super().__init__(
            name="Horizen",
            ticker_symbol="ZEN",
            address_validator=HorizenAddressValidator(),
        )
