from collections.abc import Callable, ItemsView
import threading
import weakref

from typing import Iterator, Dict, List, Set, TypeVar, Generic

T = TypeVar('T')

class ThreadSafeSet(Set[T]):
    def __init__(self):
        self._set: Set[T] = set()
        self._read_lock = threading.RLock()
        self._write_lock = threading.Lock()

    def add(self, item: T):
        with self._write_lock:
            self._set.add(item)

    def remove(self, item: T):
        with self._write_lock:
            self._set.remove(item)

    def discard(self, item: T):
        with self._write_lock:
            self._set.discard(item)

    def clear(self):
        with self._write_lock:
            self._set.clear()

    def __iter__(self) -> Iterator[T]:
        with self._read_lock:
            return iter(self._set.copy())

    def __contains__(self, item: T):
        with self._read_lock:
            return item in self._set

    def __len__(self):
        with self._read_lock:
            return len(self._set)


class ThreadSafeWeakSet(Generic[T]):
    def __init__(self):
        self._set: Set[weakref.ReferenceType[T]] = set()
        self._read_lock = threading.RLock()
        self._write_lock = threading.Lock()

    def add(self, item: T):
        with self._write_lock:
            self._set.add(weakref.ref(item))

    def remove(self, item: T):
        with self._write_lock:
            self._set.discard(weakref.ref(item))

    def discard(self, item: T):
        self.remove(item)
    
    def clear(self):
        with self._write_lock:
            self._set.clear()

    def __iter__(self) -> Iterator[T]:
        with self._read_lock:
            # Create new set with only valid references
            return iter([ref() for ref in self._set.copy() if ref() is not None])

    def __contains__(self, item: T):
        with self._read_lock:
            return weakref.ref(item) in self._set

    def __len__(self):
        with self._read_lock:
            return len(self._set)
        
    def cleanup(self):
        """Remove dead references"""
        with self._write_lock:
            dead = {ref for ref in self._set if ref() is None}
            self._set.difference_update(dead)

K = TypeVar('K')
V = TypeVar('V')
R = TypeVar('R')  # Return type for callback

class ConcurrentDict(Generic[K, V]):
    def __init__(self):
        self._dict: Dict[K, V] = {}
        self._lock = threading.RLock()
    
    def get(self, key: K, default: V = None) -> V:
        with self._lock:
            return self._dict.get(key, default)
            
    def put(self, key: K, value: V):
        with self._lock:
            self._dict[key] = value
            
    def remove(self, key: K) -> V:
        with self._lock:
            return self._dict.pop(key, None)
    
    def update(self, other: Dict[K, V]):
        with self._lock:
            self._dict.update(other)
            
    def items(self):
        with self._lock:
            return list(self._dict.items())
            
    def values(self):
        with self._lock:
            return list(self._dict.values())
    
    def with_items(self, callback: Callable[[ItemsView[K, V]], R]) -> R:
        with self._lock:
            return callback(self._dict.items())
        
class ConcurrentList(Generic[T]):
    def __init__(self):
        self._list: List[T] = []
        self._read_lock = threading.RLock()
        self._write_lock = threading.Lock()
    
    def append(self, item: T) -> None:
        with self._write_lock:
            self._list.append(item)
    
    def extend(self, items: List[T]) -> None:
        with self._write_lock:
            self._list.extend(items)
            
    def pop(self, index: int = -1) -> T:
        with self._write_lock:
            return self._list.pop(index)
            
    def remove(self, item: T) -> None:
        with self._write_lock:
            self._list.remove(item)
            
    def clear(self) -> None:
        with self._write_lock:
            self._list.clear()
            
    def insert(self, index: int, item: T) -> None:
        with self._write_lock:
            self._list.insert(index, item)
    
    def __getitem__(self, index: int) -> T:
        with self._read_lock:
            return self._list[index]
    
    def __setitem__(self, index: int, value: T) -> None:
        with self._write_lock:
            self._list[index] = value
            
    def __len__(self) -> int:
        with self._read_lock:
            return len(self._list)
            
    def __iter__(self) -> Iterator[T]:
        with self._read_lock:
            return iter(self._list.copy())
            
    def __contains__(self, item: T) -> bool:
        with self._read_lock:
            return item in self._list

class AtomicBoolean:
    def __init__(self, initial: bool = False):
        self._value = initial
        self._lock = threading.Lock()

    def get(self) -> bool:
        with self._lock:
            return self._value

    def set(self, new_value: bool) -> None:
        with self._lock:
            self._value = new_value

    def get_and_set(self, new_value: bool) -> bool:
        """Atomically sets new value and returns the old value"""
        with self._lock:
            old_value = self._value
            self._value = new_value
            return old_value

    def compare_and_set(self, expected: bool, new_value: bool) -> bool:
        """Atomically sets the value to new_value if the current value equals expected"""
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False

    def __bool__(self) -> bool:
        return self.get()

class AtomicInt:
    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def get(self) -> int:
        with self._lock:
            return self._value

    def set(self, new_value: int) -> None:
        with self._lock:
            self._value = new_value

    def get_and_set(self, new_value: int) -> int:
        """Atomically sets new value and returns the old value"""
        with self._lock:
            old_value = self._value
            self._value = new_value
            return old_value

    def compare_and_set(self, expected: int, new_value: int) -> bool:
        """Atomically sets the value to new_value if the current value equals expected"""
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False

    def add_and_get(self, delta: int) -> int:
        """Atomically adds delta and returns the new value"""
        with self._lock:
            self._value += delta
            return self._value

    def get_and_add(self, delta: int) -> int:
        """Atomically adds delta and returns the previous value"""
        with self._lock:
            old_value = self._value
            self._value += delta
            return old_value

    def increment_and_get(self) -> int:
        """Atomically increments by one and returns the new value"""
        return self.add_and_get(1)

    def decrement_and_get(self) -> int:
        """Atomically decrements by one and returns the new value"""
        return self.add_and_get(-1)

    def get_and_increment(self) -> int:
        """Atomically increments by one and returns the previous value"""
        return self.get_and_add(1)

    def get_and_decrement(self) -> int:
        """Atomically decrements by one and returns the previous value"""
        return self.get_and_add(-1)

