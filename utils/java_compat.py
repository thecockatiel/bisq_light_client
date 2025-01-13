from decimal import Decimal
import math
from pathlib import Path
import re

INTEGER_MIN_VALUE = 0x80000000
INTEGER_MAX_VALUE = 0x7fffffff
DOUBLE_MIN_VALUE = 4.9E-324

def java_arrays_byte_hashcode(bytes_array: bytes):
    result = 1
    for b in bytes_array:
        # Convert signed byte to unsigned & match Java's byte->int conversion
        b = b & 0xFF  
        result = ((31 * result) + b) & 0xFFFFFFFF
    return result - ((result & 0x80000000) << 1)

def java_string_hashcode(s: str) -> int:
    result = 0
    for c in s:
        result = ((31 * result) + ord(c)) & 0xFFFFFFFF
    return result - ((result & 0x80000000) << 1)

_equal_or_colon = re.compile(r'[=:]')

def _unescape(value: str) -> str:
    value = value.replace('\\n', '\n')
    value = value.replace('\\r', '\r')
    value = value.replace('\\t', '\t')
    value = value.replace('\\f', '\f')
    return value

def parse_resource_bundle(path: Path) -> dict[str, str]:
    with open(path, 'r', encoding='utf-8') as f:
        resources = dict[str, str]()
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle continuation lines
                while line.endswith('\\'):
                    line = line[:-1] + next(f).strip()
                
                # Split on first '=' or ':'
                key_value = re.split(_equal_or_colon, line, maxsplit=1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    # Handle escape sequences
                    value = _unescape(value)
                    resources[key] = value
        return resources

def long_unsigned_right_shift(number: int, bits: int) -> int:
    """Python equivalent of Java's >>> on longs"""   
    if number < 0:
        number = number + (1 << 64)
    return (number >> bits) & ((2 ** 64 - 1) >> bits)

def int_unsigned_right_shift(number: int, bits: int) -> int:
    """Python equivalent of Java's >>> on longs"""
    bits = bits & 31
    number = number & 0xFFFFFFFF
    return (number >> bits) & (0xFFFFFFFF >> bits)

def next_down_double(d: float) -> float:
    if math.isnan(d) or d == float('-inf'):
        return d
    if d == 0.0:
        return -DOUBLE_MIN_VALUE # Java's -Double.MIN_VALUE
    return math.nextafter(d, float('-inf'))

def get_exponent_double(value: float) -> int:
    """
    Returns the unbiased exponent of a floating point value,
    equivalent to Java's Math.getExponent(double d)
    
    If the argument is NaN or infinite, then the result is Double. MAX_EXPONENT + 1.
    If the argument is zero or subnormal, then the result is Double. MIN_EXPONENT -1.
    """
    if math.isnan(value) or math.isinf(value):
        return 1024
    
    if value == 0.0 or Decimal(value).is_subnormal():
        return -1023
    # frexp returns mantissa and exponent where value = mantissa * 2**exponent
    mantissa, exponent = math.frexp(abs(value))
    return exponent - 1

def unsigned_compare(list1: list[int], list2: list[int]) -> int:
    """equivalent of UnsignedInts.lexicographicalComparator().compare() of java's com.google.common.primitives"""
    min_len = min(len(list1), len(list2))
    for i in range(min_len):
        a = list1[i] & 0xffffffff  # Convert to unsigned 32-bit
        b = list2[i] & 0xffffffff
        if a != b:
            return -1 if a < b else 1
    return len(list1) - len(list2)  # If all equal, compare lengths

def to_unsigned_int(value: int) -> int:
    """Converts a signed int to an unsigned int"""
    return value & 0xFFFFFFFF
