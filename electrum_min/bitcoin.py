
from typing import Optional, Tuple, Union
from electrum_min import constants, segwit_addr
from electrum_min.util import BitcoinException, inv_dict, to_bytes
from .crypto import sha256d

class BaseDecodeError(BitcoinException): pass

class InvalidChecksum(BaseDecodeError):
    pass

__b58chars = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
assert len(__b58chars) == 58
__b58chars_inv = inv_dict(dict(enumerate(__b58chars)))

__b43chars = b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$*+-./:'
assert len(__b43chars) == 43
__b43chars_inv = inv_dict(dict(enumerate(__b43chars)))


def base_decode(v: Union[bytes, str], *, base: int) -> Optional[bytes]:
    """ decode v into a string of len bytes.

    based on the work of David Keijser in https://github.com/keis/base58
    """
    # assert_bytes(v)
    v = to_bytes(v, 'ascii')
    if base not in (58, 43):
        raise ValueError('not supported base: {}'.format(base))
    chars = __b58chars
    chars_inv = __b58chars_inv
    if base == 43:
        chars = __b43chars
        chars_inv = __b43chars_inv

    origlen = len(v)
    v = v.lstrip(chars[0:1])
    newlen = len(v)

    num = 0
    try:
        for char in v:
            num = num * base + chars_inv[char]
    except KeyError:
        raise BaseDecodeError('Forbidden character {} for base {}'.format(char, base))

    return num.to_bytes(origlen - newlen + (num.bit_length() + 7) // 8, 'big')


def DecodeBase58Check(psz: Union[bytes, str]) -> bytes:
    vchRet = base_decode(psz, base=58)
    payload = vchRet[0:-4]
    csum_found = vchRet[-4:]
    csum_calculated = sha256d(payload)[0:4]
    if csum_calculated != csum_found:
        raise InvalidChecksum(f'calculated {csum_calculated.hex()}, found {csum_found.hex()}')
    else:
        return payload


def b58_address_to_hash160(addr: str) -> Tuple[int, bytes]:
    addr = to_bytes(addr, 'ascii')
    _bytes = DecodeBase58Check(addr)
    if len(_bytes) != 21:
        raise Exception(f'expected 21 payload bytes in base58 address. got: {len(_bytes)}')
    return _bytes[0], _bytes[1:21]


def is_segwit_address(addr: str, *, net=None) -> bool:
    if net is None: net = constants.net
    try:
        witver, witprog = segwit_addr.decode_segwit_address(net.SEGWIT_HRP, addr)
    except Exception as e:
        return False
    return witprog is not None

def is_b58_address(addr: str, *, net: constants.AbstractNet=None) -> bool:
    if net is None: net = constants.net
    
    try:
        # test length, checksum, encoding:
        addrtype, h = b58_address_to_hash160(addr)
    except Exception as e:
        return False
    if addrtype not in [net.ADDRTYPE_P2PKH, net.ADDRTYPE_P2SH]:
        return False
    return True

def is_address(addr: str, *, net=None) -> bool:
    return is_segwit_address(addr, net=net) \
           or is_b58_address(addr, net=net)
