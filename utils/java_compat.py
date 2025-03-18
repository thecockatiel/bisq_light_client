from decimal import Decimal
import math
from pathlib import Path
import re
from typing import Any, Generic, Iterator, Optional, TypeVar

INTEGER_MIN_VALUE = 0x80000000
INTEGER_MAX_VALUE = 0x7FFFFFFF
DOUBLE_MIN_VALUE = 4.9e-324


def java_arrays_byte_hashcode(bytes_array: bytes):
    result = 1
    for b in bytes_array:
        # Convert signed byte to unsigned & match Java's byte->int conversion
        b = b & 0xFF
        result = ((31 * result) + b) & 0xFFFFFFFF
    return result - ((result & 0x80000000) << 1)


def java_string_hashcode(s: str) -> int:
    result = 0
    for c in s:
        result = ((31 * result) + ord(c)) & 0xFFFFFFFF
    return result - ((result & 0x80000000) << 1)


_equal_or_colon = re.compile(r"[=:]")


def _unescape(value: str) -> str:
    value = value.replace("\\n", "\n")
    value = value.replace("\\r", "\r")
    value = value.replace("\\t", "\t")
    value = value.replace("\\f", "\f")
    return value


def parse_resource_bundle(path: Path) -> dict[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        resources = dict[str, str]()
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Handle continuation lines
                while line.endswith("\\"):
                    line = line[:-1] + next(f).strip()

                # Split on first '=' or ':'
                key_value = re.split(_equal_or_colon, line, maxsplit=1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    # Handle escape sequences
                    value = _unescape(value)
                    resources[key] = value
        return resources


def long_unsigned_right_shift(number: int, bits: int) -> int:
    """Python equivalent of Java's >>> on longs"""
    if number < 0:
        number = number + (1 << 64)
    return (number >> bits) & ((2**64 - 1) >> bits)


def int_unsigned_right_shift(number: int, bits: int) -> int:
    """Python equivalent of Java's >>> on longs"""
    bits = bits & 31
    number = number & 0xFFFFFFFF
    return (number >> bits) & (0xFFFFFFFF >> bits)


def next_down_double(d: float) -> float:
    if math.isnan(d) or d == float("-inf"):
        return d
    if d == 0.0:
        return -DOUBLE_MIN_VALUE  # Java's -Double.MIN_VALUE
    return math.nextafter(d, float("-inf"))


def get_exponent_double(value: float) -> int:
    """
    Returns the unbiased exponent of a floating point value,
    equivalent to Java's Math.getExponent(double d)

    If the argument is NaN or infinite, then the result is Double. MAX_EXPONENT + 1.
    If the argument is zero or subnormal, then the result is Double. MIN_EXPONENT -1.
    """
    if math.isnan(value) or math.isinf(value):
        return 1024

    if value == 0.0 or Decimal(value).is_subnormal():
        return -1023
    # frexp returns mantissa and exponent where value = mantissa * 2**exponent
    mantissa, exponent = math.frexp(abs(value))
    return exponent - 1


def unsigned_compare(list1: list[int], list2: list[int]) -> int:
    """equivalent of UnsignedInts.lexicographicalComparator().compare() of java's com.google.common.primitives"""
    min_len = min(len(list1), len(list2))
    for i in range(min_len):
        a = list1[i] & 0xFFFFFFFF  # Convert to unsigned 32-bit
        b = list2[i] & 0xFFFFFFFF
        if a != b:
            return -1 if a < b else 1
    return len(list1) - len(list2)  # If all equal, compare lengths


def to_unsigned_int(value: int) -> int:
    """Converts a signed int to an unsigned int"""
    return value & 0xFFFFFFFF


def java_string_compare(s1: str, s2: str) -> int:
    min_len = min(len(s1), len(s2))
    for i in range(min_len):
        if s1[i] != s2[i]:
            return ord(s1[i]) - ord(s2[i])
    return len(s1) - len(s2)


K = TypeVar("K")
V = TypeVar("V")


class HashMap(Generic[K, V]):
    """
    A bucket-based HashMap that mimics Java's HashMap behavior.
    """

    class Entry(Generic[K, V]):
        __slots__ = ("hash", "key", "value")

        def __init__(self, hash: int, key: K, value: V) -> None:
            self.key = key
            self.value = value
            self.hash = hash

        def __repr__(self) -> str:
            # A simple representation: key:value
            return f"{self.key}:{self.value}"

    def __init__(self, initial_capacity: int = 16, load_factor: float = 0.75) -> None:
        self._capacity: int = initial_capacity
        self._load_factor: float = load_factor
        self._size: int = 0
        # Initialize a list of empty buckets.
        self._buckets: list[list[HashMap.Entry[K, V]]] = [
            [] for _ in range(self._capacity)
        ]

    def _bucket_index(self, key: K) -> int:
        return (self._hash(key) & 0x7FFFFFFF) % len(self._buckets)

    def _hash(self, key: Any) -> int:
        if key is None:
            return 0
        return (h := hash(key)) ^ (int_unsigned_right_shift(h, 16))

    def _rehash(self) -> None:
        """Double the capacity and re-distribute existing entries,
        preserving the order within each bucket as done in Java's HashMap.

        For each old bucket at index i, the new index is determined by:
          - if (key.hash & old_capacity) == 0, then index remains i;
          - else, the new index is i + old_capacity.
        """
        old_buckets = self._buckets
        old_capacity = self._capacity
        new_capacity = old_capacity * 2
        new_buckets: list[list[HashMap.Entry[K, V]]] = [[] for _ in range(new_capacity)]

        # Process each bucket from the old table.
        for i in range(old_capacity):
            bucket = old_buckets[i]
            if not bucket:
                continue
            lo_list: list[HashMap.Entry[K, V]] = []
            hi_list: list[HashMap.Entry[K, V]] = []
            for entry in bucket:
                # Use the bit mask to decide which new bucket the entry goes to.
                if entry.hash & old_capacity == 0:
                    lo_list.append(entry)
                else:
                    hi_list.append(entry)
            new_buckets[i] = lo_list
            new_buckets[i + old_capacity] = hi_list

        self._buckets = new_buckets
        self._capacity = new_capacity
        # Note: _size remains unchanged.

    def put(self, key: K, value: V) -> Optional[V]:
        """
        Associates the specified value with the specified key.
        Returns the previous value if the key existed, or None otherwise.
        """
        index = self._bucket_index(key)
        key_hash = self._hash(key)
        bucket = self._buckets[index]
        for entry in bucket:
            if entry.key == key:
                old_value = entry.value
                entry.value = value
                return old_value
        # Key not found; append a new entry.
        bucket.append(HashMap.Entry(key_hash, key, value))
        self._size += 1
        if self._size > self._capacity * self._load_factor:
            self._rehash()
        return None

    def get(self, key: K) -> Optional[V]:
        """Returns the value associated with the key, or None if not found."""
        index = self._bucket_index(key)
        for entry in self._buckets[index]:
            if entry.key == key:
                return entry.value
        return None

    def remove(self, key: K) -> Optional[V]:
        """
        Removes the mapping for a key if present.
        Returns the removed value or None if the key was not found.
        """
        index = self._bucket_index(key)
        bucket = self._buckets[index]
        for i, entry in enumerate(bucket):
            if entry.key == key:
                removed_value = entry.value
                del bucket[i]
                self._size -= 1
                return removed_value
        return None

    def containsKey(self, key: K) -> bool:
        """Returns True if the map contains the specified key."""
        index = self._bucket_index(key)
        return any(entry.key == key for entry in self._buckets[index])

    def containsValue(self, value: V) -> bool:
        """Returns True if the map contains one or more keys mapped to the value."""
        return any(entry.value == value for bucket in self._buckets for entry in bucket)

    def size(self) -> int:
        """Returns the number of key-value mappings."""
        return self._size

    def clear(self) -> None:
        """Removes all mappings from the map."""
        self._capacity = 16
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0

    def keys(self) -> Iterator[K]:
        """Iterate over keys (bucket order)."""
        for bucket in self._buckets:
            for entry in bucket:
                yield entry.key

    def values(self) -> Iterator[V]:
        """Iterate over values (bucket order)."""
        for bucket in self._buckets:
            for entry in bucket:
                yield entry.value

    def items(self) -> Iterator[tuple[K, V]]:
        """Iterate over (key, value) pairs (bucket order)."""
        for bucket in self._buckets:
            for entry in bucket:
                yield (entry.key, entry.value)

    def __iter__(self) -> Iterator[K]:
        return self.items()

    def __getitem__(self, key: K) -> V:
        value = self.get(key)
        if value is None and not self.containsKey(key):
            raise KeyError(key)
        return value  # type: ignore

    def __setitem__(self, key: K, value: V) -> None:
        self.put(key, value)

    def __delitem__(self, key: K) -> None:
        if self.remove(key) is None:
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        return self.containsKey(key)  # type: ignore

    def __len__(self) -> int:
        return self._size
