from dataclasses import dataclass
from typing import ClassVar, Optional

@dataclass(frozen=True, kw_only=True)
class AddressValidationResult:
    """
    Value object representing the result of validating an Asset address.
    Various factory methods are provided for typical use cases.
    
    @since 0.7.0
    """
    is_valid: bool
    message: str
    i18n_key: str

    def is_valid(self) -> bool:
        return self.is_valid

    def get_i18n_key(self) -> str:
        return self.i18n_key

    def get_message(self) -> str:
        return self.message

    # Class-level constant for valid address
    _VALID_ADDRESS: ClassVar['AddressValidationResult'] = None 
    @classmethod
    def valid_address(cls) -> 'AddressValidationResult':
        if cls._VALID_ADDRESS is None:
            cls._VALID_ADDRESS = cls(is_valid=True, message="", i18n_key="")
        return cls._VALID_ADDRESS

    @classmethod
    def invalid_address(cls, cause: Optional[Exception | str], 
                       i18n_key: str = "validation.altcoin.invalidAddress") -> 'AddressValidationResult':
        message = str(cause) if cause else ""
            
        return cls(is_valid=False, message=message, i18n_key=i18n_key)

    @classmethod
    def invalid_structure(cls) -> 'AddressValidationResult':
        return cls.invalid_address("", "validation.altcoin.wrongStructure")
