from collections.abc import Callable
from typing import Any, Iterable, Literal, Optional, Set, TypeVar, Generic, Union
from dataclasses import dataclass, field

T = TypeVar("T")
R = TypeVar("R")

K = TypeVar("K")
V = TypeVar("V")

@dataclass
class SimplePropertyChangeEvent(Generic[T]):
    old_value: T
    new_value: T

@dataclass
class ObservableChangeEvent(Generic[T]):
    added_elements: Optional[Iterable[T]] = field(default=None)
    removed_elements: Optional[Iterable[T]] = field(default=None)


class SimpleProperty(Generic[T]):
    def __init__(self, 
                 initial_value: T = None,
                 on_add_listener: Optional[Callable[[int], None]] = None,
                 on_remove_listener: Optional[Callable[[int], None]] = None,
                 on_accessed: Optional[Callable[[], None]] = None):
        self._value = initial_value
        self._listeners = set()
        self.on_accessed = on_accessed
        self.on_add_listener = on_add_listener
        self.on_remove_listener = on_remove_listener 

    def get(self) -> T:
        if self.on_accessed:
            self.on_accessed()
        return self._value

    def set(self, value: T) -> None:
        if self._value != value:
            old_value = self._value
            self._value = value
            self._notify_listeners(SimplePropertyChangeEvent(old_value, value))

    def add_listener(self, listener: Callable[[SimplePropertyChangeEvent[T]], None]) -> Callable[[], None]:
        if listener not in self._listeners:
            self._listeners.add(listener)
            if self.on_add_listener:
                self.on_add_listener(len(self._listeners))
        return lambda: self.remove_listener(listener)

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
        for listener in self._listeners.copy():
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
    
    def __repr__(self):
        return f"SimpleProperty({self._value})"

    def __str__(self):
        return str(self._value)

def combine_simple_properties(*properties: SimpleProperty[R], transform: Callable[[list[R]], T]) -> SimpleProperty[T]:
    eval_cache = None
    
    def evaluate():
        return transform([p.get() for p in properties])

    def on_change(*_):
        nonlocal result, eval_cache
        eval_cache = evaluate()
        result.value = eval_cache
    
    def on_add_listener(new_len: int):
        if new_len == 1:
            # we started to get subscribers
            for prop in properties:
                prop.add_listener(on_change)
        
    def on_remove_listener(new_len: int):
        if new_len == 0:
            # we lost all subscribers
            for prop in properties:
                prop.remove_listener(on_change)
    
    result = SimpleProperty(None, on_add_listener, on_remove_listener, on_accessed=on_change)
    
    return result
    
    
class ObservableSet(set[T]):
    def __init__(self, *args):
        super().__init__(*args)
        self._listeners: Set[Callable[[ObservableChangeEvent[T]], None]] = set()
    
    def add_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]):
        self._listeners.add(listener)
        
    def remove_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]):
        self._listeners.discard(listener)
        
    def remove_all_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]):
        self._listeners.discard(listener)
        
    def _notify(self, e: ObservableChangeEvent[T]):
        for listener in self._listeners.copy():
            listener(e)
            
    def add(self, element: T) -> bool:
        """
        returns true if the element was added, false if it was already present.
        """
        if element in self:
            return False
        super().add(element)
        self._notify(ObservableChangeEvent([element]))
        return True
        
    def remove(self, element: T) -> None:
        """
        returns true if the element was removed, false if it was NOT present.
        This set does NOT raise KeyError for non-existing elements.
        """
        if element not in self:
            return False
        super().remove(element)
        self._notify(ObservableChangeEvent(None, [element]))
        return True
        
    def clear(self) -> None:
        elements = list(self)
        super().clear()
        self._notify(ObservableChangeEvent(None, elements))
        
    def update(self, *others: Iterable[T]) -> bool:
        before = self.copy()
        super().update(*others)
        added_elements = self - before
        if len(added_elements) > 0:
            self._notify(ObservableChangeEvent(added_elements))
            return True
        return False


class ObservableMap(dict[K, V]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._listeners: Set[ObservableChangeEvent[tuple[K,V]]] = set()
    
    def add_listener(self, listener: Callable[[ObservableChangeEvent[tuple[K,V]]], None]):
        self._listeners.add(listener)
        
    def remove_listener(self, listener: Callable[[ObservableChangeEvent[tuple[K,V]]], None]):
        self._listeners.discard(listener)
        
    def remove_all_listeners(self):
        self._listeners.clear()
        
    def _notify(self, e: ObservableChangeEvent[tuple[K,V]]):
        for listener in self._listeners.copy():
            listener(e)
            
    def __setitem__(self, key: K, value: V) -> None:
        super().__setitem__(key, value)
        self._notify(ObservableChangeEvent([(key, value)]))
        
    def __delitem__(self, key: K) -> None:
        if key in self:
            value = self[key]
            super().__delitem__(key)
            self._notify(ObservableChangeEvent(None, [(key, value)]))
            
    def clear(self) -> None:
        l = list(self.items())
        super().clear()
        self._notify(ObservableChangeEvent(None, l))
        
    def update(self, m: Iterable[tuple[K, V]]=None, **kwargs) -> None:
        if m:
            remove_changes = []
            add_changes = []
            new_items = dict(m).items()
            for k, v in new_items:
                existed = k in self
                super().__setitem__(k, v) # to not trigger notifs until after all changes are done
                if existed:
                    remove_changes.append((k, v))
                add_changes.append((k, v))
            if len(remove_changes) > 0 or len(add_changes) > 0:
                self._notify(ObservableChangeEvent(add_changes if add_changes else None, remove_changes if remove_changes else None))


class ObservableList(list[T]):
    def __init__(self, *args):
        super().__init__(*args)
        self._listeners: Set[Callable[[ObservableChangeEvent[T]], None]] = set()
    
    def add_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]):
        self._listeners.add(listener)
        
    def remove_listener(self, listener: Callable[[ObservableChangeEvent[T]], None]):
        self._listeners.discard(listener)
        
    def remove_all_listeners(self):
        self._listeners.clear()
        
    def _notify(self, e: ObservableChangeEvent[T]):
        for listener in self._listeners.copy():
            listener(e)
            
    def append(self, element: T) -> None:
        super().append(element)
        self._notify(ObservableChangeEvent([element]))
        
    def extend(self, iterable: Iterable[T]) -> None:
        l = list(iterable)
        super().extend(iterable)
        if len(l) > 0:
            self._notify(ObservableChangeEvent(l))
        
    def insert(self, index: int, element: T) -> None:
        super().insert(index, element)
        self._notify(ObservableChangeEvent([element]))
        
    def remove(self, element: T) -> None:
        if element in self:
            super().remove(element)
            self._notify(ObservableChangeEvent(None, [element]))
            
    def pop(self, index: int = -1) -> T:
        element = super().pop(index)
        self._notify(ObservableChangeEvent(None, [element]))
        return element
        
    def clear(self) -> None:
        elements = list(self)
        super().clear()
        self._notify(ObservableChangeEvent(None, elements))
        
    def __setitem__(self, index, element: T) -> None:
        if self[index] == element:
            return
        removed = self[index]
        added = element
        super().__setitem__(index, element)
        self._notify(ObservableChangeEvent([added], [removed]))
        
    def __delitem__(self, index) -> None:
        element = self[index]
        super().__delitem__(index)
        self._notify(ObservableChangeEvent(None, [element]))

def raise_required() -> None:
    raise ValueError("This field is required and cannot be unset")
