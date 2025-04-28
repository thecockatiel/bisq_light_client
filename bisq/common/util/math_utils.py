from math import isnan, pow
from typing import Union
from bisq.common.setup.log_setup import get_ctx_logger
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException

_infinities = (float("inf"), float("-inf"))


# NOTE: on edge cases values where different between java and python, but in general it's ok.
class MathUtils:
    @staticmethod
    def round_double(
        value: float, precision: int, rounding_mode: int = ROUND_HALF_UP
    ) -> float:
        if precision < 0:
            raise IllegalArgumentException("Precision cannot be negative")
        if not isinstance(value, (int, float)) or value in _infinities or isnan(value):
            raise IllegalArgumentException(f"Expected a finite float, but found {value}")

        try:
            dec = Decimal(str(value))
            rounded = dec.quantize(Decimal("0.1") ** precision, rounding=rounding_mode)
            return float(rounded)
        except (InvalidOperation, ValueError) as e:
            logger = get_ctx_logger(__name__)
            logger.error(str(e))
            return 0.0

    @staticmethod
    def round_double_to_long(value: float, rounding_mode: int = ROUND_HALF_UP) -> int:
        if not isinstance(value, (int, float)) or value in _infinities or isnan(value):
            raise IllegalArgumentException(f"Expected a finite float, but found {value}")

        try:
            dec = Decimal(str(value))
            rounded = dec.quantize(Decimal("1"), rounding=rounding_mode)
            return int(rounded)
        except (InvalidOperation, ValueError) as e:
            logger = get_ctx_logger(__name__)
            logger.error(str(e))
            return 0

    @staticmethod
    def scale_up_by_power_of_10(value: Union[float, int], exponent: int) -> float:
        factor = pow(10, exponent)
        return value * factor

    @staticmethod
    def scale_down_by_power_of_10(value: Union[float, int], exponent: int) -> float:
        factor = pow(10, exponent)
        return value / factor

    @staticmethod
    def exact_multiply(value1: float, value2: float) -> float:
        result = Decimal(str(value1)) * Decimal(str(value2))
        return float(result)
