from abc import abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

_T = TypeVar("_T")


class TradeResultHandler(Generic[_T]):

    @abstractmethod
    def __call__(self, trade: _T):
        pass
