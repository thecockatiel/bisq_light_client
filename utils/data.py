from collections.abc import Callable
from typing import Any, Optional, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar("T")


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
            self._listeners.remove(listener)
            if self.on_remove_listener:
                self.on_remove_listener(len(self._listeners))

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
    