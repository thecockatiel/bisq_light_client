from abc import ABC
from typing import Optional
from bisq.common.handlers.result_handler import ResultHandler

class GracefulShutDownHandler(ABC):
    def graceful_shut_down(self, result_handler: Optional[ResultHandler] = None) -> None:
        result_handler()
