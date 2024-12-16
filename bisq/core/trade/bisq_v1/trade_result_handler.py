from abc import abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

_T = TypeVar("_T")


class TradeResultHandler(Callable[[_T], None], Generic[_T]):

    @abstractmethod
    def handle_result(self, trade: _T) -> None:
        pass

    def __call__(self, trade: _T):
        return self.handle_result(trade)
