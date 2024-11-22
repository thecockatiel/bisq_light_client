from math import isnan
from bisq.common.setup.log_setup import get_logger
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

logger = get_logger(__name__)

_infinities = (float('inf'), float('-inf'))

# NOTE: on edge cases values where different between java and python, but in general it's ok.
class MathUtils:
    @staticmethod
    def round_double(value: float, precision: int, rounding_mode: int = ROUND_HALF_UP) -> float:
        if precision < 0:
            raise ValueError("Precision cannot be negative")
        if not isinstance(value, (int, float)) or value in _infinities or isnan(value):
            raise ValueError(f"Expected a finite float, but found {value}")
            
        try:
            dec = Decimal(str(value))
            rounded = dec.quantize(Decimal('0.1') ** precision, rounding=rounding_mode)
            return float(rounded)
        except (InvalidOperation, ValueError) as e:
            logger.error(str(e))
            return 0.0

