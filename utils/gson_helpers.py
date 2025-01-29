from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class TypeAdapter(Generic[T], ABC):
    @abstractmethod
    def read(self, json_element: str) -> T:
        """Read JSON and convert to object"""
        pass

    @abstractmethod
    def write(self, obj: T) -> str:
        """Convert object to JSON string"""
        pass
