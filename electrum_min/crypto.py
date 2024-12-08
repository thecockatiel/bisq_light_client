import hashlib
import hmac
from typing import Union

from electrum_min.util import to_bytes

def sha256(x: Union[bytes, str]) -> bytes:
    x = to_bytes(x, 'utf8')
    return bytes(hashlib.sha256(x).digest())

def sha256d(x: Union[bytes, str]) -> bytes:
    x = to_bytes(x, 'utf8')
    out = bytes(sha256(sha256(x)))
    return out

def hmac_oneshot(key: bytes, msg: bytes, digest) -> bytes:
    return hmac.digest(key, msg, digest)
