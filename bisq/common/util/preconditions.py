from typing import Any
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


def check_argument(expression: Any, errorMessage: Any):
    if not expression:
        raise IllegalArgumentException(str(errorMessage))
