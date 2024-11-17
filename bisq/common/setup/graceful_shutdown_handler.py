from abc import ABC
from typing import Callable, Optional

class GracefulShutDownHandler(ABC):
    def graceful_shut_down(self, result_handler: Optional[Callable[[], None]] = None) -> None:
        pass
