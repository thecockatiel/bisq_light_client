from collections.abc import Callable
from typing import Any, Generic, Iterator, Sequence, Type, TypeVar, Union
from functools import wraps

_T = TypeVar("_T")
_R = TypeVar("_R")

class LazySequenceWrapper(Generic[_T, _R]):
    """returns a wrapper around a sequence that will lazily do the wrapping on each element when accessed"""
    
    def __init__(self, get_sequence: Callable[[], Sequence[_T]], wrapper: Callable[[Type[_T], int], _R]):
        self._get_sequence = get_sequence
        self._sequence: Sequence[_T] = None
        self._wrapper = wrapper
        self._initialized_idx = {}
        
    def _check_and_get_sequence(self) -> Sequence[_T]:
        if self._sequence is None:
            self._sequence = self._get_sequence()
        return self._sequence
        
    def __getitem__(self, key: Union[int, slice]) -> _R:
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(len(self)))]
        if key not in self._initialized_idx:
            self._initialized_idx[key] = self._wrapper(self._check_and_get_sequence()[key], key)
        return self._initialized_idx[key]
    
    def __delitem__(self, index: int) -> None:
        del self._initialized_idx[index]
        del self._sequence[index]
    
    def __len__(self) -> int: 
        return len(self._check_and_get_sequence())
    
    def __iter__(self) -> Iterator[_R]: 
        for index, _ in enumerate(self._check_and_get_sequence()):
            yield self[index]
    
    def __contains__(self, item: _R) -> bool:
        return any(item == i for i in self)
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LazySequenceWrapper):
            return False
        return self._sequence == other._sequence
    
    def __str__(self):
        return "LazySequenceWrapper(initialized=" + str(self._initialized_idx) + ")"
