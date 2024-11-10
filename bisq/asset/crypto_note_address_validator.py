from dataclasses import dataclass, field
from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bisq.asset.crypto_note_utils import MoneroBase58


@dataclass(frozen=True)
class CryptoNoteAddressValidator(AddressValidator):
    """
    AddressValidator for Base58-encoded Cryptonote addresses.
    """

    validate_checksum: bool = field(default=True)
    valid_prefixes: list[int] = field(default_factory=list)

    def validate(self, address: str) -> AddressValidationResult:
        try:
            prefix = MoneroBase58.decode_address(address, self.validate_checksum)
            if prefix in self.valid_prefixes:
                return AddressValidationResult.valid_address()
            else:
                return AddressValidationResult.invalid_address(
                    f"invalid address prefix {prefix}"
                )
        except Exception as e:
            return AddressValidationResult.invalid_address(e)
