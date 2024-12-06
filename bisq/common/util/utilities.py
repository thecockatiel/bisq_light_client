import platform
from utils.dir import user_data_dir

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