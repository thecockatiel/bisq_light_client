from typing import Optional
from bisq.core.locale.res import Res
from bisq.core.util.validation.input_validation_result import InputValidationResult
from bisq.core.util.validation.input_validator import InputValidator
import re

class RegexValidator(InputValidator):
    def __init__(self):
        self._pattern: re.Pattern = None
        self.error_message: str = None
    
    @property
    def pattern(self):
        return self._pattern.pattern if self._pattern is not None else None
    
    @pattern.setter
    def pattern(self, pattern: str):
        self._pattern = re.compile(pattern)

    def validate(self, input_str: Optional[str]):
        result = InputValidationResult(True)
        message = Res.get("validation.pattern", self.pattern) if self.error_message is None else self.error_message
        test_str = "" if input_str is None else input_str

        if self._pattern is None:
            return result

        if not re.match(self.pattern, test_str):
            result = InputValidationResult(False, message)

        return result
