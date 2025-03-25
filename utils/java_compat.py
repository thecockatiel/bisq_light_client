from ctypes import c_int32, c_int8
from decimal import Decimal
import math
from pathlib import Path
import re
from typing import Any, Generic, Iterable, Iterator, Optional, TypeVar
from functools import cmp_to_key

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

def java_bytes_hashcode(array: bytes) -> int:
    if array is None:
        return 0
    
    result = 1
    for element in array:
        result = 31 * result + c_int8(element).value
    
    return c_int32(result).value

def java_string_compare(s1: str, s2: str) -> int:
    min_len = min(len(s1), len(s2))
    for i in range(min_len):
        if s1[i] != s2[i]:
            return ord(s1[i]) - ord(s2[i])
    return len(s1) - len(s2)

def java_cmp_str(s: str) -> Any:
    pass # hack to colorize the function and trigger auto import

java_cmp_str = cmp_to_key(java_string_compare)

K = TypeVar("K")
V = TypeVar("V")


class HashMap(Generic[K, V]):
    __slots__ = ("_capacity", "_load_factor", "_size", "_table", "_mod_count")

    def __init__(
        self,
        initial_items: Iterable[tuple[K, V]] = None,
        *,
        initial_capacity: int = 16,
        load_factor: float = 0.75,
    ) -> None:
        self._capacity: int = initial_capacity
        self._load_factor: float = load_factor
        self._size: int = 0
        self._mod_count: int = 0
        self._table: list[Optional[HashMap.Node[K, V]]] = [None] * self._capacity
        if initial_items is not None:
            for key, value in initial_items:
                self.put(key, value)

    class Node(Generic[K, V]):
        __slots__ = ("hash", "key", "value", "next")

        def __init__(self, hash: int, key: K, value: V, next_node=None) -> None:
            self.key = key
            self.value = value
            self.hash = hash
            self.next = next_node

        def __repr__(self) -> str:
            return f"{self.key}:{self.value}"

    def _hash(self, key: K) -> int:
        if key is None:
            return 0
        if isinstance(key, str):
            h = java_string_hashcode(key)
        else:
            h = hash(key)
        return h ^ (int_unsigned_right_shift(h, 16))
    
    def _index_for(self, hash_val: int) -> int:
        return hash_val & (self._capacity - 1)

    def _get_node(self, key: K) -> Optional["HashMap.Node[K, V]"]:
        hash_val = self._hash(key)
        index = self._index_for(hash_val)
        node = self._table[index]
        
        while node is not None:
            if node.hash == hash_val and (node.key == key or (key is not None and key == node.key)):
                return node
            node = node.next
        return None

    def _resize(self) -> None:
        old_capacity = self._capacity
        if old_capacity >= 0x40000000:  # MAXIMUM_CAPACITY in Java (2^30)
            return
        
        new_capacity = old_capacity * 2
        old_table = self._table
        self._capacity = new_capacity
        self._table = [None] * new_capacity
        
        if self._size > 0:
            for j in range(old_capacity):
                node = old_table[j]
                if node is not None:
                    old_table[j] = None  # Help GC
                    if node.next is None:
                        # No collision, just copy node to new table
                        self._table[node.hash & (new_capacity - 1)] = node
                    else:
                        # Handle collision by rebuilding the chain
                        lo_head = lo_tail = hi_head = hi_tail = None
                        while node is not None:
                            next_node = node.next
                            
                            # Determine which bucket the node goes in new table
                            if (node.hash & old_capacity) == 0:
                                # Low bucket
                                if lo_tail is None:
                                    lo_head = node
                                else:
                                    lo_tail.next = node
                                lo_tail = node
                            else:
                                # High bucket
                                if hi_tail is None:
                                    hi_head = node
                                else:
                                    hi_tail.next = node
                                hi_tail = node
                            
                            node = next_node
                        
                        # Place the chains in their new locations
                        if lo_tail is not None:
                            lo_tail.next = None
                            self._table[j] = lo_head
                        if hi_tail is not None:
                            hi_tail.next = None
                            self._table[j + old_capacity] = hi_head

    def put(self, key: K, value: V) -> Optional[V]:
        hash_val = self._hash(key)
        index = self._index_for(hash_val)
        
        node = self._table[index]
        if node is None:
            # Create new node at the beginning of the bucket
            self._table[index] = self.Node(hash_val, key, value)
            self._size += 1
            self._mod_count += 1
            if self._size > self._capacity * self._load_factor:
                self._resize()
            return None
        
        # Check existing nodes in the bucket
        prev = None
        while node is not None:
            k = node.key
            if node.hash == hash_val and (k == key or (key is not None and key == k)):
                # Key exists, replace value
                old_value = node.value
                node.value = value
                return old_value
            prev = node
            node = node.next
        
        # Add new node to end of bucket chain
        prev.next = self.Node(hash_val, key, value)
        self._size += 1
        self._mod_count += 1
        if self._size > self._capacity * self._load_factor:
            self._resize()
        return None

    def get(self, key: K) -> Optional[V]:
        node = self._get_node(key)
        return node.value if node else None

    def remove(self, key: K) -> Optional[V]:
        hash_val = self._hash(key)
        index = self._index_for(hash_val)
        
        node = self._table[index]
        prev = None
        
        while node is not None:
            if node.hash == hash_val and (node.key == key or (key is not None and key == node.key)):
                # Found node to remove
                if prev is None:
                    self._table[index] = node.next
                else:
                    prev.next = node.next
                
                self._size -= 1
                self._mod_count += 1
                return node.value
            
            prev = node
            node = node.next
        
        return None

    def containsKey(self, key: K) -> bool:
        return self._get_node(key) is not None

    def containsValue(self, value: V) -> bool:
        if value is None:
            for i in range(self._capacity):
                node = self._table[i]
                while node is not None:
                    if node.value is None:
                        return True
                    node = node.next
        else:
            for i in range(self._capacity):
                node = self._table[i]
                while node is not None:
                    if value == node.value:
                        return True
                    node = node.next
        return False

    def size(self) -> int:
        return self._size
    
    def isEmpty(self) -> bool:
        return self._size == 0

    def clear(self) -> None:
        tab = self._table
        for i in range(self._capacity):
            tab[i] = None
        self._size = 0
        self._mod_count += 1

    def keySet(self) -> set[K]:
        result = set()
        for k in self.keys():
            result.add(k)
        return result

    def keys(self) -> Iterator[K]:
        for i in range(self._capacity):
            node = self._table[i]
            while node is not None:
                yield node.key
                node = node.next

    def values(self) -> Iterator[V]:
        for i in range(self._capacity):
            node = self._table[i]
            while node is not None:
                yield node.value
                node = node.next

    def items(self) -> Iterator[tuple[K, V]]:
        for i in range(self._capacity):
            node = self._table[i]
            while node is not None:
                yield (node.key, node.value)
                node = node.next

    def __iter__(self) -> Iterator[tuple[K, V]]:
        return self.items()

    def __getitem__(self, key: K) -> V:
        value = self.get(key)
        if value is None and not self.containsKey(key):
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        self.put(key, value)

    def __delitem__(self, key: K) -> None:
        if self.remove(key) is None:
            raise KeyError(key)

    def __contains__(self, key: K) -> bool:
        return self.containsKey(key)

    def __len__(self) -> int:
        return self._size
