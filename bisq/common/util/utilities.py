from collections.abc import Callable
import platform
import threading
from typing import Any, Generic, TypeVar
from utils.dir import user_data_dir
import random
import string

from utils.java_compat import int_unsigned_right_shift

def get_sys_info():
    return f"System info: os.name={platform.system()}; os.version={platform.version()}; os.arch={platform.machine()}; platform={platform.platform()}"

def encode_to_hex(bytes_: bytes, allow_none: bool) -> str:
    if allow_none:
        return bytes.hex(bytes_) if bytes_ is not None else "None"
    assert bytes_ is not None, "bytes_ must not be None at encode_to_hex"
    return bytes_.hex()

def bytes_as_hex_string(data: bytes) -> str:
    return encode_to_hex(data, allow_none=True)

def get_system_home_directory():
    return user_data_dir().parent

def get_random_prefix(min_length: int, max_length: int) -> str:
    length = random.randint(min_length, max_length)
    
    char_choices = [
        string.ascii_letters,
        string.digits,
        string.ascii_letters + string.digits
    ]
    chars = random.choice(char_choices)
    result = ''.join(random.choice(chars) for _ in range(length))
    
    case_choices = [str.upper, str.lower, lambda x: x]
    case_transformer = random.choice(case_choices)
    return case_transformer(result)

def integer_to_byte_array(int_value: int, num_bytes: int) -> bytes:
    bytes_ = bytearray(num_bytes)
    for i in range(num_bytes - 1, -1, -1):
        bytes_[i] = int_value & 0xFF
        int_value = int_unsigned_right_shift(int_value, 8)
    return bytes(bytes_)

def byte_array_to_integer(bytes_: bytes) -> int:
    result = 0
    for byte in bytes_:
        result = (result << 8) | (byte & 0xFF)
    # Mask to 32-bit signed integer range
    result = result & 0xFFFFFFFF
    # Convert to signed integer if necessary
    if result >= 0x80000000:
        result -= 0x100000000
    return result

def copy_right_aligned(src: bytes, new_length: int) -> bytes:
    dest = bytearray(new_length)
    src_pos = max(len(src) - new_length, 0)
    dest_pos = max(new_length - len(src), 0)
    dest[dest_pos:] = src[src_pos:src_pos + new_length - dest_pos]
    return bytes(dest)

def bytes_to_ints_be(bytes_data: bytes) -> list[int]:
    result = []
    for i in range(0, len(bytes_data) - 3, 4):
        val = int.from_bytes(bytes_data[i:i + 4], byteorder='big', signed=True)
        result.append(val)
    return result

def ints_to_bytes_be(ints: list[int]) -> bytes:
    result = bytearray(len(ints) * 4)
    for i, v in enumerate(ints):
        pos = i * 4
        result[pos] = (v >> 24) & 0xFF
        result[pos + 1] = (v >> 16) & 0xFF
        result[pos + 2] = (v >> 8) & 0xFF
        result[pos + 3] = v & 0xFF
    return bytes(result)

def is_qubes_os() -> bool:
    return platform.system().lower() == "linux" and "qubes" in platform.platform().lower()


_T = TypeVar('_T')

class WaitableResultHandler(Generic[_T], Callable[[_T], None]):
    def __init__(self):
        self._result_container: dict[str, _T] = {"value": None}
        self._completion_event = threading.Event()

    def __call__(self, result: _T):
        self._result_container["value"] = result
        self._completion_event.set()
    
    def wait(self) -> _T:
        self._completion_event.wait()
        return self._result_container["value"]

import secrets
import string

def get_random_id(length=8):
    chars = string.ascii_letters + string.digits
    # using secrets for better randomness
    return ''.join(secrets.choice(chars) for _ in range(length))
