
from typing import Any, Optional, Set
import secrets

def parse_max_spend(amt: Any) -> Optional[int]:
    """Checks if given amount is "spend-max"-like.
    Returns None or the positive integer weight for "max". Never raises.

    When creating invoices and on-chain txs, the user can specify to send "max".
    This is done by setting the amount to '!'. Splitting max between multiple
    tx outputs is also possible, and custom weights (positive ints) can also be used.
    For example, to send 40% of all coins to address1, and 60% to address2:
    ```
    address1, 2!
    address2, 3!
    ```
    """
    if not (isinstance(amt, str) and amt and amt[-1] == '!'):
        return None
    if amt == '!':
        return 1
    x = amt[:-1]
    try:
        x = int(x)
    except ValueError:
        return None
    if x > 0:
        return x
    return None

def to_string(x, enc) -> str:
    if isinstance(x, (bytes, bytearray)):
        return x.decode(enc)
    if isinstance(x, str):
        return x
    else:
        raise TypeError("Not a string or bytes like object")

def to_bytes(something, encoding='utf8') -> bytes:
    """
    cast string to bytes() like object, but for python2 support it's bytearray copy
    """
    if isinstance(something, bytes):
        return something
    if isinstance(something, str):
        return something.encode(encoding)
    elif isinstance(something, bytearray):
        return bytes(something)
    else:
        raise TypeError("Not a string or bytes like object")

def chunks(items, size: int):
    """Break up items, an iterable, into chunks of length size."""
    if size < 1:
        raise ValueError(f"size must be positive, not {repr(size)}")
    for i in range(0, len(items), size):
        yield items[i: i + size]
        
def inv_dict(d: dict):
    return {v: k for k, v in d.items()}


def all_subclasses(cls) -> Set:
    """Return all (transitive) subclasses of cls."""
    res = set(cls.__subclasses__())
    for sub in res.copy():
        res |= all_subclasses(sub)
    return res

bfh = bytes.fromhex

def is_hex_str(text: Any) -> bool:
    if not isinstance(text, str): return False
    try:
        b = bytes.fromhex(text)
    except Exception:
        return False
    # forbid whitespaces in text:
    if len(text) != 2 * len(b):
        return False
    return True

def assert_bytes(*args):
    """
    porting helper, assert args type
    """
    try:
        for x in args:
            assert isinstance(x, (bytes, bytearray))
    except Exception:
        print('assert bytes failed', list(map(type, args)))
        raise

def randrange(bound: int) -> int:
    """Return a random integer k such that 1 <= k < bound, uniformly
    distributed across that range."""
    # secrets.randbelow(bound) returns a random int: 0 <= r < bound,
    # hence transformations:
    return secrets.randbelow(bound - 1) + 1

class BitcoinException(Exception): pass


class InvalidPassword(Exception):
    def __init__(self, message: Optional[str] = None):
        self.message = message

    def __str__(self):
        if self.message is None:
            return _("Incorrect password")
        else:
            return str(self.message)
        
class WalletFileException(Exception):
    def __init__(self, message='', *, should_report_crash: bool = False):
        Exception.__init__(self, message)
        self.should_report_crash = should_report_crash

        
def versiontuple(v):
    return tuple(map(int, (v.split("."))))

class classproperty(property):
    """~read-only class-level @property
    from https://stackoverflow.com/a/13624858 by denis-ryzhkov
    """
    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)
