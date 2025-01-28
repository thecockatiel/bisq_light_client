from typing import TYPE_CHECKING
import zlib
import hashlib
import struct
from electrum_min.crypto import ripemd

try:
    from Crypto.Hash import keccak
except:
    # pycryptodomex
    from Cryptodome.Hash import keccak
    

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_payload import NetworkPayload

def get_sha256_hash(data: bytes):
    return hashlib.sha256(data).digest()


def get_sha256_hash_from_string(message: str):
    return get_sha256_hash(message.encode("utf-8"))


def get_sha256_hash_from_integer(data: int):
    return get_sha256_hash(struct.pack(">I", data))


def get_sha256_ripemd160_hash(data: bytes):
    # This will use the RIPEMD160 hash of SHA256(data)
    sha256_digest = get_sha256_hash(data)
    return ripemd(sha256_digest)


def get_ripemd160_hash(data: bytes):
    return ripemd(data)

def get_keccak1600_hash(data: bytes):
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()

def get_crc32_hash(data: bytes):
    return zlib.crc32(data)

def get_32_byte_hash(data: "NetworkPayload") -> bytes:
    return get_sha256_hash(data.serialize_for_hash())
