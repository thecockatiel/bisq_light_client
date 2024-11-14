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
            return item in self._set

    def __len__(self):
        with self._read_lock:
            return len(self._set)

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
        