from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class DependencyProvider(Generic[T], ABC):
    @abstractmethod
    def get(self) -> T:
        pass
