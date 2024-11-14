from types import MappingProxyType
from typing import TypeVar, Generic

K = TypeVar('K')
V = TypeVar('V')

class ImmutableMap(Generic[K, V]):

    def __init__(self, data: dict[K, V] = {}) -> None:
        self._data = MappingProxyType(data)
    
    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"ImmutableMap({self._data})"
    
    def __contains__(self, key: K) -> bool:
        return key in self._data

    def get(self, key: K, default: V = None) -> V:
        return self._data.get(key, default)

    def copy(self) -> dict[K, V]:
        return self._data.copy()
    
    def items(self):
        return self._data.items()

    # Prevent modifications
    def __setitem__(self, key, value):
        raise TypeError("ImmutableMap does not support item assignment")

    def __delitem__(self, key):
        raise TypeError("ImmutableMap does not support item deletion")