from bisq.core.locale.res import Res
from typing import Optional

from bisq.core.util.validation.input_validation_result import InputValidationResult


class InputValidator:
    def __init__(self):
        self.allow_empty = False

    def validate(self, input_str: Optional[str]) -> InputValidationResult:
        return self.validate_if_not_empty(input_str)

    def validate_if_not_empty(self, input_str: str) -> InputValidationResult:
        if self.allow_empty:
            return InputValidationResult(True)
        elif input_str is None or input_str.strip() == "":
            return InputValidationResult(False, Res.get("validation.empty"))
        else:
            return InputValidationResult(True)

    def is_positive_number(self, input_str: Optional[str]) -> bool:
        try:
            return input_str is not None and int(input_str) >= 0
        except Exception:
            return False

    def is_number_with_fixed_length(self, input_str: str, length: int) -> bool:
        return self.is_positive_number(input_str) and len(input_str) == length

    def is_number_in_range(self, input_str: str, min_length: int, max_length: int) -> bool:
        return self.is_positive_number(input_str) and min_length <= len(input_str) <= max_length

    def is_string_with_fixed_length(self, input_str: Optional[str], length: int) -> bool:
        return input_str is not None and len(input_str) == length

    def is_string_in_range(self, input_str: Optional[str], min_length: int, max_length: int) -> bool:
        return input_str is not None and min_length <= len(input_str) <= max_length
