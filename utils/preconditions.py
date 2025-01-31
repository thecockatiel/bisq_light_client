from typing import Any, Union
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


def check_argument(expression: Union[bool, Any], errorMessage: Union[str, Exception, Any]):
    if not expression:
        raise IllegalArgumentException(str(errorMessage))
