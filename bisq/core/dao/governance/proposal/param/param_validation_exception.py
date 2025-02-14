from enum import IntEnum
from typing import Union


class ParamValidationException(Exception):

    class ERROR(IntEnum):
        SAME = 0
        NO_CHANGE_POSSIBLE = 1
        TOO_LOW = 2
        TOO_HIGH = 3

    def __init__(
        self,
        message_or_exception: Union[str, Exception],
        param_error: "ParamValidationException.ERROR",
        *args,
    ):
        super().__init__(message_or_exception, *args)
        self.error = param_error

    def __str__(self):
        return (
            f"ParamValidationException{{\n"
            f"    error={self.error}\n"
            f"}} {super().__str__()}"
        )
