from abc import ABC
from collections.abc import Callable
from typing import Optional
from bisq.common.handlers.result_handler import ResultHandler

class GracefulShutDownHandler(ABC):
    def graceful_shut_down(self, result_handler: Optional[Callable[[int], None]] = None) -> None:
        result_handler(0)
