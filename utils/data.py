from collections.abc import Callable
from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar("T")


@dataclass
class PropertyChangeEvent(Generic[T]):
    old_value: T
    new_value: T


class SimpleObjectProperty(Generic[T]):
    def __init__(self, initial_value: T = None):
        self._value = initial_value
        self._listeners = []

    def get(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        if self._value != value:
            old_value = self._value
            self._value = value
            self._notify_listeners(PropertyChangeEvent(old_value, value))

    def add_listener(self, listener: Callable[[PropertyChangeEvent[T]], None]) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[PropertyChangeEvent[T]], None]) -> None:
        self._listeners.remove(listener)

    def _notify_listeners(self, event: PropertyChangeEvent[T]) -> None:
        for listener in self._listeners:
            listener(event)

    # Property decorator syntax support
    @property
    def value(self) -> T:
        return self.get()

    @value.setter
    def value(self, new_value: T) -> None:
        self.set(new_value)
