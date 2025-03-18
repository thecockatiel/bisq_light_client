from typing import Any, Union
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException


def check_argument(
    expression: Union[bool, Any], error_message: Union[str, Exception, Any] = ""
):
    if not expression:
        raise IllegalArgumentException(str(error_message))


def check_state(
    expression: Union[bool, Any], error_message: Union[str, Exception, Any] = ""
):
    if not expression:
        raise IllegalStateException(str(error_message))


def check_not_null(reference: Any, error_message: str = "Reference is null") -> Any:
    if reference is None:
        raise AssertionError(error_message)
    return reference
