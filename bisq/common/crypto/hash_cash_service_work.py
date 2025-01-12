from ctypes import c_byte
import struct
from bisq.common.crypto.hash import get_sha256_hash

from utils.java_compat import (
    get_exponent_double,
    int_unsigned_right_shift,
    next_down_double,
)


def number_of_leading_zeros_byte(byte: int) -> int:
    byte = c_byte(byte).value
    if byte <= 0:
        return 8 if byte == 0 else 0
    n = 7
    if byte >= 1 << 4:
        n -= 4
        byte = int_unsigned_right_shift(byte, 4)
    if byte >= 1 << 2:
        n -= 2
        byte = int_unsigned_right_shift(byte, 2)
    return n - int_unsigned_right_shift(byte, 1)


def number_of_leading_zeros(bytes_data: bytes) -> int:
    number_of_leading_zeros = 0
    for i, byte in enumerate(bytes_data):
        number_of_leading_zeros += number_of_leading_zeros_byte(byte)
        if number_of_leading_zeros < 8 * (i + 1):
            break
    return number_of_leading_zeros


def to_sha256_hash(payload: bytes, challenge: bytes, counter: int) -> bytes:
    pre_image = payload + challenge + struct.pack(">q", counter)
    return get_sha256_hash(pre_image)


def to_num_leading_zeros(difficulty: float) -> int:
    return get_exponent_double(max(next_down_double(difficulty), 0.5)) + 1


def do_mint(payload: bytes, challenge: bytes, difficulty: float) -> tuple[int, bytes]:
    log2_difficulty = to_num_leading_zeros(difficulty)
    counter = 0
    while True:
        counter += 1
        hash_result = to_sha256_hash(payload, challenge, counter)
        if number_of_leading_zeros(hash_result) > log2_difficulty:
            break

    solution = struct.pack(">q", counter)
    return counter, solution
