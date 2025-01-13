# see https://github.com/bisq-network/bisq/blob/v1.9.18/common/src/main/java/bisq/common/crypto/Equihash.java
# for more information

import hashlib
import math
from typing import Optional
import struct

from bisq.common.util.utilities import (
    bytes_to_ints_be,
    copy_right_aligned,
    ints_to_bytes_be,
)
from utils.java_compat import (
    get_exponent_double,
    int_unsigned_right_shift,
    to_unsigned_int,
    unsigned_compare,
)


class Equihash:
    HASH_BIT_LENGTH = 256
    MEAN_SOLUTION_COUNT_PER_NONCE = 2.0
    """Mean solution count per nonce for Equihash puzzles with unit difficulty. """

    def __init__(self, n: int, k: int, difficulty: float):
        assert (
            k > 0 and k < self.HASH_BIT_LENGTH / 32
        ), f"Tree depth k must be a positive integer less than {self.HASH_BIT_LENGTH / 32}"
        assert (
            n > 0 and n < self.HASH_BIT_LENGTH and n % (k + 1) == 0
        ), f"Collision bit count n must be a positive multiple of k + 1 and less than {self.HASH_BIT_LENGTH}"
        assert (
            n / (k + 1) < 30
        ), f"Sub-collision bit count n / (k + 1) must be less than 30, got {n / (k + 1)}"

        self.k = k
        self.input_num = 1 << k
        self.input_bits = n // (k + 1) + 1
        self.N = 1 << self.input_bits
        self.table_capacity = int(self.N * 1.1)
        self.hash_upper_bound = self.get_hash_upper_bound(difficulty)

    @staticmethod
    def get_hash_upper_bound(difficulty: float) -> list[int]:
        return bytes_to_ints_be(
            copy_right_aligned(
                Equihash.inverse_difficulty_minus_one(difficulty).to_bytes(
                    (Equihash.HASH_BIT_LENGTH + 7) // 8,
                    "big",
                ),
                Equihash.HASH_BIT_LENGTH // 8,
            )
        )

    @staticmethod
    def inverse_difficulty_minus_one(difficulty: float) -> int:
        assert difficulty >= 1.0, "Difficulty must be at least 1."
        exponent = get_exponent_double(difficulty) - 52
        mantissa = math.ldexp(difficulty, -exponent)
        if mantissa == float("inf"):
            mantissa = 9223372036854775807
        else:
            mantissa = int(mantissa)
        shift_bits = Equihash.HASH_BIT_LENGTH - exponent
        if shift_bits >= 0:
            numerator = 1 << shift_bits
        else:
            numerator = 1 >> -shift_bits
        numerator = numerator + mantissa - 1
        inverse = numerator // mantissa - 1
        return max(inverse, 0)

    @staticmethod
    def adjust_difficulty(real_difficulty: float) -> float:
        """
        Adjust the provided difficulty to take the variable number of puzzle solutions per
        nonce into account, so that the expected number of attempts needed to solve a given
        puzzle equals the reciprocal of the provided difficulty.
        """
        logp_input = -1.0 / max(real_difficulty, 1.0)
        if logp_input > -1:
            logp = math.log1p(logp_input)
        elif logp_input == -1.0:
            logp = float("-inf")
        else:
            logp = math.nan
        if logp == 0:
            return float("inf")
        return max(
            -Equihash.MEAN_SOLUTION_COUNT_PER_NONCE / logp,
            1.0,
        )

    def find_collisions(self, table: "XorTable", is_partial: bool) -> "XorTable":
        new_hash_width = table.hash_width - 1 if is_partial else 0
        new_index_tuple_width = table.index_tuple_width * 2
        new_table_values = []

        # Use IntListMultimap instead of regular dict
        index_multimap = IntListMultimap(self.N // 2)

        for i in range(table.num_rows):
            row = table.get_row(i)
            # Get collisions from multimap
            for colliding_index in index_multimap.get(row[0]):
                colliding_row = table.get_row(colliding_index)

                if is_partial:
                    # XOR the hash values
                    for j in range(1, table.hash_width):
                        new_table_values.append(colliding_row[j] ^ row[j])
                else:
                    # Check if remaining hash values match
                    if colliding_row[1 : table.hash_width] != row[1 : table.hash_width]:
                        continue

                # Add index tuples from both rows
                new_table_values.extend(colliding_row[table.hash_width :])
                new_table_values.extend(row[table.hash_width :])

            # Add current index to multimap
            index_multimap.put(row[0], i)

        return XorTable(new_hash_width, new_index_tuple_width, tuple(new_table_values))

    @staticmethod
    def sort_inputs(inputs: list[int]) -> list[int]:
        sublist_stack: list[list[int]] = []
        for input_val in inputs:
            top_sublist = [input_val]
            while sublist_stack and len(sublist_stack[-1]) == len(top_sublist):
                other = sublist_stack.pop()
                # Changed comparison logic to match Java's behavior exactly
                if unsigned_compare(other, top_sublist) < 0:
                    top_sublist = other + top_sublist
                else:
                    top_sublist = top_sublist + other
            sublist_stack.append(top_sublist)
        return sublist_stack.pop() if sublist_stack else []

    def with_hash_prefix(self, seed: bytes, nonce: int):
        return EquihashWithHashPrefix(seed + nonce.to_bytes(4, "big"), self)


def deserialize_equihash_puzzle_solution(data: bytes, equihash: "Equihash"):
    bit_len = 64 + equihash.input_num * equihash.input_bits
    byte_len = (bit_len + 7) // 8

    # Validate input length
    if len(data) != byte_len:
        raise ValueError(
            f"Incorrect solution byte length. Expected {byte_len} but got {len(data)}"
        )

    # Check padding bits are zero
    if byte_len > 0:
        if (data[byte_len - 1] << ((bit_len + 7 & 7) + 1)) & 0xFF != 0:
            raise ValueError("Nonzero padding bits found at end of solution byte array")

    # Pad bytes to multiple of 4
    padded_data = data if (byte_len & 3) == 0 else data + bytes((-byte_len & 3))

    # Read nonce from first 8 bytes
    nonce = (int.from_bytes(padded_data[0:4], "big") << 32) | int.from_bytes(
        padded_data[4:8], "big"
    )

    # Read inputs
    inputs = []
    off = 0
    buf = 0
    idx = 8

    for _ in range(equihash.input_num):
        if off < equihash.input_bits:
            buf = (buf << 32) | int.from_bytes(padded_data[idx : idx + 4], "big")
            off += 32
            idx += 4
        off -= equihash.input_bits
        inputs.append(int_unsigned_right_shift(buf, off) & (equihash.N - 1))

    return nonce, inputs


def find_equihash_solution(equihash: "Equihash", seed: bytes):
    nonce = 0
    while True:
        result = equihash.with_hash_prefix(seed, nonce).find_inputs()
        if result is not None:
            return EquihashPuzzleSolution(equihash, seed, nonce, list(result))
        nonce += 1


def count_all_solutions_for_nonce(equihash: "Equihash", seed: bytes, nonce: int) -> int:
    return len(set(equihash.with_hash_prefix(seed, nonce).stream_inputs_hits()))


class EquihashPuzzleSolution:
    def __init__(
        self, equihash: "Equihash", seed: bytes, nonce: int, inputs: list[int]
    ):
        self.equihash = equihash
        self.seed = seed
        self.nonce = nonce
        self.inputs = inputs

    def verify(self) -> bool:
        return self.equihash.with_hash_prefix(self.seed, self.nonce).verify(self.inputs)

    def serialize(self) -> bytes:
        input_num = len(self.inputs)
        bit_len = 64 + input_num * self.equihash.input_bits
        byte_len = (bit_len + 7) // 8
        
        # Create padded bytes array (padding to multiple of 4)
        padded_bytes = bytearray((byte_len + 3) & -4)
        
        # Pack nonce into first 8 bytes as two 32-bit ints
        struct.pack_into('>II', padded_bytes, 0, 
                        to_unsigned_int(self.nonce >> 32), 
                        to_unsigned_int(self.nonce))
        
        off = 64
        buf = 0
        int_idx = 8  # Start after nonce (8 bytes = 2 ints)
        
        for v in self.inputs:
            off -= self.equihash.input_bits
            # Convert to unsigned long
            buf |= (to_unsigned_int(v) & 0xFFFFFFFF) << off
            
            if off <= 32:
                # Pack the top 32 bits
                struct.pack_into('>I', padded_bytes, int_idx, to_unsigned_int(buf >> 32))
                int_idx += 4
                buf <<= 32
                off += 32
        
        if off < 64:
            # Pack remaining bits
            struct.pack_into('>I', padded_bytes, int_idx, to_unsigned_int(buf >> 32))
        
        # Return exact length if not multiple of 4
        return bytes(padded_bytes if (byte_len & 3) == 0 else padded_bytes[:byte_len])

    def __str__(self) -> str:
        return f"EquihashPuzzleSolution(nonce={self.nonce}, inputs={str(self.inputs)})"


class EquihashWithHashPrefix:
    def __init__(self, prefix_bytes: bytes, equihash: "Equihash"):
        self.prefix_bytes = prefix_bytes
        self.equihash = equihash

    def hash_inputs(self, *inputs: int) -> list[int]:
        digest = hashlib.blake2b(digest_size=Equihash.HASH_BIT_LENGTH // 8)
        digest.update(self.prefix_bytes)
        input_bytes = ints_to_bytes_be(inputs)
        digest.update(input_bytes)
        return bytes_to_ints_be(digest.digest())

    def stream_inputs_hits(self):
        table = self.compute_all_hashes()
        for i in range(self.equihash.k):
            table = self.equihash.find_collisions(table, i + 1 < self.equihash.k)

        def row_generator():
            for i in range(table.num_rows):
                row = table.get_row(i)
                if len(set(row)) == self.equihash.input_num:
                    sorted_inputs = Equihash.sort_inputs(list(row))
                    if self.test_difficulty_condition(sorted_inputs):
                        yield tuple(sorted_inputs)

        return row_generator()

    def find_inputs(self) -> Optional[tuple[int, ...]]:
        return next(self.stream_inputs_hits(), None)

    def compute_all_hashes(self) -> "XorTable":
        table_values = []
        for i in range(self.equihash.N):
            hash_result = self.hash_inputs(i)
            for j in range(self.equihash.k + 2):
                if j <= self.equihash.k:
                    table_values.append(hash_result[j] & (self.equihash.N // 2 - 1))
                else:
                    table_values.append(i)
        return XorTable(self.equihash.k + 1, 1, tuple(table_values))

    def test_difficulty_condition(self, inputs: list[int]) -> bool:
        difficulty_hash = self.hash_inputs(*inputs)
        for h, b in zip(difficulty_hash, self.equihash.hash_upper_bound):
            if h < b:
                return True
            if h > b:
                return False
        return True

    def verify(self, inputs: list[int]) -> bool:
        if (
            len(inputs) != self.equihash.input_num
            or len(set(inputs)) < self.equihash.input_num
        ):
            return False

        if any(i < 0 or i >= self.equihash.N for i in inputs):
            return False

        if inputs != Equihash.sort_inputs(inputs):
            return False

        if not self.test_difficulty_condition(inputs):
            return False

        hash_block_sums = [0] * (self.equihash.k + 1)
        for i, input_val in enumerate(inputs):
            hash_result = self.hash_inputs(input_val)
            for j in range(self.equihash.k + 1):
                hash_block_sums[j] ^= hash_result[j] & (self.equihash.N // 2 - 1)

            ii = i + 1 + self.equihash.input_num
            j = 0
            while ii & 1 == 0:
                if hash_block_sums[j] != 0:
                    return False
                ii //= 2
                j += 1

        return True


class XorTable:
    def __init__(self, hash_width: int, index_tuple_width: int, values: tuple[int]):
        self.hash_width = hash_width
        self.index_tuple_width = index_tuple_width
        self.values = values
        self.row_width = hash_width + index_tuple_width
        self.num_rows = (len(values) + self.row_width - 1) // self.row_width

    def get_row(self, index: int) -> tuple[int]:
        start = index * self.row_width
        end = start + self.hash_width + self.index_tuple_width
        return self.values[start:end]


class IntListMultimap:
    def __init__(self, key_upper_bound: int):
        self.short_lists = [0] * (key_upper_bound * 4)
        self.overspill_map: dict[int, list[int]] = {}  # Changed to store lists

    def get(self, key: int):
        # Check shortLists first
        for i in range(4):
            idx = key * 4 + i
            if self.short_lists[idx] < 0:
                yield ~self.short_lists[idx]

        # Then check overspill
        if key in self.overspill_map:
            yield from self.overspill_map[key]

    def put(self, key: int, value: int):
        for i in range(4):
            idx = key * 4 + i
            if self.short_lists[idx] == 0:
                self.short_lists[idx] = ~value
                return

        # Initialize list if key doesn't exist
        if key not in self.overspill_map:
            self.overspill_map[key] = []
        self.overspill_map[key].append(value)
