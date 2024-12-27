from typing import Any, Generic, Iterable, TypeVar
from collections import OrderedDict

T = TypeVar("T")
R = TypeVar("R")

class OrderedSet(Generic[T]):
    def __init__(self, iterable=None):
        self._dict = OrderedDict[T, Any].fromkeys([] if iterable is None else iterable)
        
    def add(self, item: T):
        self._dict[item] = None
        
    def discard(self, item: T):
        self._dict.pop(item, None)
        
    def remove(self, item: T):
        del self._dict[item]
        
    def pop(self):
        item,_ = self._dict.popitem()
        return item
        
    def clear(self):
        self._dict.clear()
        
    def update(self, items: Iterable[T]):
        self._dict.update(dict.fromkeys(items))
        
    def __iter__(self):
        return iter(self._dict)
        
    def __len__(self):
        return len(self._dict)
        
    def __contains__(self, item: T):
        return item in self._dict
        
    def __repr__(self):
        return f"{self.__class__.__name__}({list(self)})"
        
    def union(self, other):
        return OrderedSet(list(self) + list(other))
        
    def intersection(self, other):
        return OrderedSet(item for item in self if item in other)
        
    def difference(self, other):
        return OrderedSet(item for item in self if item not in other)
    
    def copy(self):
        return OrderedSet[T](self)
    
    def symmetric_difference(self, other):
        if not isinstance(other, OrderedSet):
            other = OrderedSet(other)
        return OrderedSet(item for item in self._dict.keys() ^ other._dict.keys())
    
    def issubset(self, other: "OrderedSet[T]"):
        return all(item in other for item in self)
    
    def issuperset(self, other: "OrderedSet[T]"):
        return all(item in self for item in other)
    
    def intersection_update(self, other: "OrderedSet[T]"):
        self._dict = dict.fromkeys(self.intersection(other))
        
    def difference_update(self, other: "OrderedSet[T]"):
        self._dict = dict.fromkeys(self.difference(other))
        
    def symmetric_difference_update(self, other: "OrderedSet[T]"):
        self._dict = dict.fromkeys(self.symmetric_difference(other))
    
    def __eq__(self, other):
        if not isinstance(other, OrderedSet) or not isinstance(other, set):
            return False
        return list(self) == list(other)
    
    def __or__(self, other):
        return self.union(other)
    
    def __and__(self, other):
        return self.intersection(other)
    
    def __sub__(self, other):
        return self.difference(other)
    
    def __xor__(self, other):
        return self.symmetric_difference(other)
    
    def __ior__(self, other):
        self.update(other)
        return self
    
    def __iand__(self, other):
        self.intersection_update(other)
        return self
    
    def __isub__(self, other):
        self.difference_update(other)
        return self
    
    def __ixor__(self, other):
        self.symmetric_difference_update(other)
        return self
