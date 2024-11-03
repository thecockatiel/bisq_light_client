from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from Crypto.Hash import RIPEMD160

import struct


def get_sha256_hash(data: bytes):
    hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
    hasher.update(data)
    return hasher.finalize()


def get_sha256_hash_from_string(message: str):
    return get_sha256_hash(message.encode("utf-8"))


def get_sha256_hash_from_integer(data: int):
    return get_sha256_hash(struct.pack(">I", data))


def get_sha256_ripemd160_hash(data: bytes):
    # This will use the RIPEMD160 hash of SHA256(data)
    sha256_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
    sha256_hash.update(data)
    sha256_digest = sha256_hash.finalize()

    h = RIPEMD160.new()
    h.update(sha256_digest)
    return h.digest()


def get_ripemd160_hash(data: bytes):
    h = RIPEMD160.new()
    h.update(data)
    return h.digest()