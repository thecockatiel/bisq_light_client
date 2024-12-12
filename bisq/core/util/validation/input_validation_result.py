from typing import Callable, Optional, List
from functools import reduce

class InputValidationResult:
    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message

    def and_(self, next_result: 'InputValidationResult') -> 'InputValidationResult':
        if self.is_valid:
            return next_result
        return self

    def __str__(self) -> str:
        return f"ValidationResult{{isValid={self.is_valid}, errorMessage='{self.error_message}'}}"

    def error_message_equals(self, other: Optional['InputValidationResult']) -> bool:
        if self is other:
            return True
        if other is None:
            return False
        return self.error_message == other.error_message

    def and_validation(self, input_str: str, *validators: Callable[[str], 'InputValidationResult']) -> 'InputValidationResult':
        """
        This function validates the input with array of validator functions.
        If any function validation result is false, it short circuits
        as in && (and) operation.
        """
        result = None
        for validator in validators:
            result = validator(input_str)
            if not result.is_valid:
                return result
        return result
