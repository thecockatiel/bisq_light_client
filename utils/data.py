from collections.abc import Callable
from typing import Any, Iterable, Optional, Set, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar("T")

K = TypeVar("K")
V = TypeVar("V")

@dataclass
class SimplePropertyChangeEvent(Generic[T]):
    old_value: T
    new_value: T


class SimpleProperty(Generic[T]):
    def __init__(self, initial_value: T = None, on_add_listener: Optional[Callable[[int], None]] = None, on_remove_listener: Optional[Callable[[int], None]] = None):
        self._value = initial_value
        self._listeners = set()
        self.on_add_listener = on_add_listener
        self.on_remove_listener = on_remove_listener 

    def get(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        if self._value != value:
            old_value = self._value
            self._value = value
            self._notify_listeners(SimplePropertyChangeEvent(old_value, value))

    def add_listener(self, listener: Callable[[SimplePropertyChangeEvent[T]], None]) -> None:
        if listener not in self._listeners:
            self._listeners.add(listener)
            if self.on_add_listener:
                self.on_add_listener(len(self._listeners))

    def remove_listener(self, listener: Callable[[SimplePropertyChangeEvent[T]], None]) -> None:
        if listener in self._listeners:
            self._listeners.discard(listener)
            if self.on_remove_listener:
                self.on_remove_listener(len(self._listeners))
                
    def remove_all_listeners(self) -> None:
        self._listeners.clear()
        if self.on_remove_listener:
            self.on_remove_listener(0)

    def _notify_listeners(self, event: SimplePropertyChangeEvent[T]) -> None:
        for listener in self._listeners:
            listener(event)

    # Property decorator syntax support
    @property
    def value(self) -> T:
        return self.get()

    @value.setter
    def value(self, new_value: T) -> None:
        self.set(new_value)
        
    def __eq__(self, value: "SimpleProperty[T]") -> bool:
        if isinstance(value, SimpleProperty):
            return self._value == value._value
        else:
            return self._value == value
    
    def __hash__(self) -> int:
        return hash(self._value)


__unset_value = "UNSET"

def combine_simple_properties(*properties: SimpleProperty, transform: Callable[[list[Any]], T]) -> SimpleProperty[T]:
    results = [__unset_value] * len(properties)
    listeners = {}

    def on_change(i: int, e: SimplePropertyChangeEvent):
        nonlocal result
        results[i] = e.new_value
        
        # check if all results are no longer UNSET
        if __unset_value not in results:
            result.value = transform(results)
    
    def on_add_listener(new_len: int):
        if new_len == 1:
            # we started to get subscribers
            for i, prop in enumerate(properties):
                listener = lambda e, i=i: on_change(i, e)
                listeners[i] = listener
                prop.add_listener(listener)
        
    def on_remove_listener(new_len: int):
        if new_len == 0:
            # we lost all subscribers
            for i, prop in enumerate(properties):
                prop.remove_listener(listeners[i])
            
    result: SimpleProperty[T] = SimpleProperty(None, on_add_listener, on_remove_listener)
    
    return result
    
    
class ObservableSet(set[T]):
    def __init__(self, *args):
        super().__init__(*args)
        self._listeners: Set[Callable] = set()
    
    def add_listener(self, listener: Callable[['ObservableSet', str, T], None]):
        self._listeners.add(listener)
        
    def remove_listener(self, listener: Callable[['ObservableSet', str, T], None]):
        self._listeners.discard(listener)
        
    def remove_all_listener(self, listener: Callable[['ObservableSet', str, T], None]):
        self._listeners.discard(listener)
        
    def _notify(self, operation: str, element: T = None):
        for listener in self._listeners:
            listener(self, operation, element)
            
    def add(self, element: T) -> bool:
        """
        returns true if the element was added, false if it was already present.
        """
        if element in self:
            return False
        super().add(element)
        self._notify('add', element)
        return True
        
    def remove(self, element: T) -> None:
        """
        returns true if the element was removed, false if it was NOT present.
        This set does NOT raise KeyError for non-existing elements.
        """
        if element not in self:
            return False
        super().remove(element)
        self._notify('remove', element)
        return True
        
    def clear(self) -> None:
        super().clear()
        self._notify('clear')
        
    def update(self, *others: Iterable[T]) -> bool:
        initial_size = len(self)
        super().update(*others)
        if len(self) > initial_size:
            self._notify('update')
            return True
        return False


class ObservableMap(dict[K, V]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._listeners: Set[Callable] = set()
    
    def add_listener(self, listener: Callable[['ObservableMap', str, K, V], None]):
        self._listeners.add(listener)
        
    def remove_listener(self, listener: Callable[['ObservableMap', str, K, V], None]):
        self._listeners.discard(listener)
        
    def remove_all_listeners(self):
        self._listeners.clear()
        
    def _notify(self, operation: str, key: K = None, value: V = None):
        for listener in self._listeners:
            listener(self, operation, key, value)
            
    def __setitem__(self, key: K, value: V) -> None:
        super().__setitem__(key, value)
        self._notify('set', key, value)
        
    def __delitem__(self, key: K) -> None:
        if key in self:
            value = self[key]
            super().__delitem__(key)
            self._notify('delete', key, value)
            
    def clear(self) -> None:
        super().clear()
        self._notify('clear')
        
    def update(self, other=None, **kwargs) -> None:
        super().update(other, **kwargs)
        self._notify('update')


class ObservableList(list[T]):
    def __init__(self, *args):
        super().__init__(*args)
        self._listeners: Set[Callable] = set()
    
    def add_listener(self, listener: Callable[['ObservableList', str, T], None]):
        self._listeners.add(listener)
        
    def remove_listener(self, listener: Callable[['ObservableList', str, T], None]):
        self._listeners.discard(listener)
        
    def remove_all_listeners(self):
        self._listeners.clear()
        
    def _notify(self, operation: str, element: T = None):
        for listener in self._listeners:
            listener(self, operation, element)
            
    def append(self, element: T) -> None:
        super().append(element)
        self._notify('append', element)
        
    def extend(self, iterable: Iterable[T]) -> None:
        l = list(iterable)
        super().extend(iterable)
        if len(l) > 1:
            self._notify('extend')
        if len(l) == 1:
            self._notify('append', l[0])
        
    def insert(self, index: int, element: T) -> None:
        super().insert(index, element)
        self._notify('insert', element)
        
    def remove(self, element: T) -> None:
        if element in self:
            super().remove(element)
            self._notify('remove', element)
            
    def pop(self, index: int = -1) -> T:
        element = super().pop(index)
        self._notify('remove', element)
        return element
        
    def clear(self) -> None:
        super().clear()
        self._notify('clear')
        
    def __setitem__(self, index, element: T) -> None:
        super().__setitem__(index, element)
        self._notify('set', element)
        
    def __delitem__(self, index) -> None:
        element = self[index]
        super().__delitem__(index)
        self._notify('remove', element)

