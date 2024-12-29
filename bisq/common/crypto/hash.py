from typing import TYPE_CHECKING
from cryptography.hazmat.primitives import hashes
from Crypto.Hash import RIPEMD160
from Crypto.Hash import keccak
import zlib
import hashlib

import struct

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

    h = RIPEMD160.new()
    h.update(sha256_digest)
    return h.digest()


def get_ripemd160_hash(data: bytes):
    h = RIPEMD160.new()
    h.update(data)
    return h.digest()

def get_keccak1600_hash(data: bytes):
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()

def get_crc32_hash(data: bytes):
    return zlib.crc32(data)

def get_32_byte_hash(data: "NetworkPayload") -> bytes:
    return get_sha256_hash(data.serialize_for_hash())
