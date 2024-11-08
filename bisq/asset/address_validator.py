from abc import ABC, abstractmethod

from bisq.asset.address_validation_result import AddressValidationResult 

class AddressValidator(ABC):
    """
    an Asset address validation base class
    
    Since: 0.7.0
    """
    
    @abstractmethod
    def validate(self, address: str) -> AddressValidationResult:
        pass