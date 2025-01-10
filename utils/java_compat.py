from pathlib import Path
import re


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
