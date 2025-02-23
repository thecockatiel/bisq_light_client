from typing import Any, Union
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


def check_argument(expression: Union[bool, Any], errorMessage: Union[str, Exception, Any] = ""):
    if not expression:
        raise IllegalArgumentException(str(errorMessage))


def check_state(expression: Union[bool, Any], errorMessage: Union[str, Exception, Any] = ""):
    if not expression:
        raise IllegalStateException(str(errorMessage))
