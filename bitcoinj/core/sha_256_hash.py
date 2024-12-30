from functools import total_ordering
import hashlib
from typing import Union


@total_ordering
class Sha256Hash:
    """
    A Sha256Hash just wraps a byte[] so that equals and hashcode work correctly, allowing it to be used as keys in a map.
    It also checks that the length is correct and provides a bit more type safety.
    """

    LENGTH = 32  # bytes
    ZERO_HASH = None  # Initialized after class definition

    def __init__(self, *, raw_hash_bytes: bytes = None, hex_string: str = None):
        """only pass one of the parameters to the constructor"""
        if raw_hash_bytes is not None and hex_string is not None:
            raise ValueError(
                "Either raw_hash_bytes or hex_string must be passed, but not both"
            )
        if raw_hash_bytes is not None:
            self.hash_bytes = raw_hash_bytes
        elif hex_string is not None:
            self.hash_bytes = bytes.fromhex(hex_string)
        else:
            raise ValueError("Either raw_hash_bytes or hex_string must be passed")

    @staticmethod
    def wrap(raw_hash_bytes_or_hex_str: Union[bytes, str]) -> "Sha256Hash":
        """Creates a new instance that wraps the given hash value."""
        if isinstance(raw_hash_bytes_or_hex_str, bytes):
            return Sha256Hash(raw_hash_bytes=raw_hash_bytes_or_hex_str)
        return Sha256Hash(raw_hash_bytes=bytes.fromhex(raw_hash_bytes_or_hex_str))
    
    @staticmethod
    def of(contents: bytes) -> "Sha256Hash":
        """Creates a new instance containing the calculated (one-time) hash of the given bytes."""
        return Sha256Hash.wrap(Sha256Hash.hash(contents))

    @staticmethod
    def twice_of(contents: bytes, contents2: bytes = None) -> "Sha256Hash":
        if contents2 is not None:
            return Sha256Hash.wrap(Sha256Hash.hash_two_inputs(contents, contents2))
        return Sha256Hash.wrap(Sha256Hash.hash_twice(contents))

    @staticmethod
    def hash(input: bytes, offset: int = 0, length: int = None) -> "Sha256Hash":
        """Calculates the SHA-256 hash of the given bytes."""
        if length is None:
            length = len(input)
        m = hashlib.sha256()
        m.update(input[offset : offset + length])
        return m.digest()

    @staticmethod
    def hash_twice(input: bytes, offset: int = 0, length: int = None) -> "Sha256Hash":
        return Sha256Hash.hash(Sha256Hash.hash(input, offset, length))

    @staticmethod
    def hash_two_inputs_ranges(
        input1: bytes,
        offset1: int,
        length1: int,
        input2: bytes,
        offset2: int,
        length2: int,
    ) -> "Sha256Hash":
        m = hashlib.sha256()
        m.update(input1[offset1 : offset1 + length1])
        m.update(input2[offset2 : offset2 + length2])
        return m.digest()


    @staticmethod
    def hash_two_inputs(
        input1: bytes,
        input2: bytes,
    ) -> "Sha256Hash":
        m = hashlib.sha256()
        m.update(input1)
        m.update(input2)
        return m.digest()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sha256Hash):
            return False
        if self.hash_bytes is None or other.hash_bytes is None:
            return False
        return self.hash_bytes == other.hash_bytes

    def __hash__(self) -> int:
        """
        Returns the last four bytes of the wrapped hash. This should be unique enough to be a suitable hash code even for
        blocks, where the goal is to try and get the first bytes to be zeros (i.e. the value as a big integer lower
        than the target value).
        """

        return int.from_bytes(self.hash_bytes[-4:], byteorder="big")

    def __str__(self):
        return self.hash_bytes.hex()

    def __lt__(self, other: "Sha256Hash") -> bool:
        """
        Implements comparison between two Sha256Hash objects.
        This enables sorting and all comparison operations.
        """
        if not isinstance(other, Sha256Hash):
            return NotImplemented

        # Compare bytes from most significant to least significant
        for i in range(self.LENGTH - 1, -1, -1):
            this_byte = self.hash_bytes[i] & 0xFF
            other_byte = other.hash_bytes[i] & 0xFF
            if this_byte != other_byte:
                return this_byte < other_byte
        return False

Sha256Hash.ZERO_HASH = Sha256Hash.wrap(bytes(Sha256Hash.LENGTH))
