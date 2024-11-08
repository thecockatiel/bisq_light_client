from dataclasses import dataclass
from typing import ClassVar, Optional

@dataclass
class AddressValidationResult:
    """
    Value object representing the result of validating an Asset address.
    Various factory methods are provided for typical use cases.
    
    @since 0.7.0
    """
    is_valid: bool
    message: str
    i18n_key: str

    # Class-level constant for valid address
    _VALID_ADDRESS: ClassVar['AddressValidationResult'] = None  # Will be initialized after class definition

    def is_valid(self) -> bool:
        return self.is_valid

    def get_i18n_key(self) -> str:
        return self.i18n_key

    def get_message(self) -> str:
        return self.message

    @classmethod
    def valid_address(cls) -> 'AddressValidationResult':
        if cls._VALID_ADDRESS is None:
            cls._VALID_ADDRESS = cls(True, "", "")
        return cls._VALID_ADDRESS

    @classmethod
    def invalid_address(cls, cause: Optional[Exception | str], 
                       i18n_key: str = "validation.altcoin.invalidAddress") -> 'AddressValidationResult':
        message = str(cause) if cause else ""
            
        return cls(False, message, i18n_key)

    @classmethod
    def invalid_structure(cls) -> 'AddressValidationResult':
        return cls.invalid_address("", "validation.altcoin.wrongStructure")

# Initialize the class-level constant
AddressValidationResult.valid_address()