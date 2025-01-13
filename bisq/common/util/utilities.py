import platform
from utils.dir import user_data_dir
import random
import string

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

def copy_right_aligned(src: bytes, new_length: int) -> bytes:
    dest = bytearray(new_length)
    src_pos = max(len(src) - new_length, 0)
    dest_pos = max(new_length - len(src), 0)
    dest[dest_pos:] = src[src_pos:src_pos + new_length - dest_pos]
    return bytes(dest)

def bytes_to_ints_be(bytes_data: bytes) -> list[int]:
    result = []
    for i in range(0, len(bytes_data) - 3, 4):
        val = (bytes_data[i] << 24) | (bytes_data[i + 1] << 16) | (bytes_data[i + 2] << 8) | bytes_data[i + 3]
        result.append(val)
    return result
