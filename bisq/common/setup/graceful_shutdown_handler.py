from abc import ABC
from collections.abc import Callable
from typing import Optional
from bisq.common.handlers.result_handler import ResultHandler

class GracefulShutDownHandler(Callable[[Optional[ResultHandler]], None], ABC):
    def graceful_shut_down(self, result_handler: Optional[ResultHandler] = None) -> None:
        pass
    
    def __call__(self, result_handler: Optional[ResultHandler] = None) -> None:
        self.graceful_shut_down(result_handler)