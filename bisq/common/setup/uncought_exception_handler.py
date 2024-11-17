from abc import ABC, abstractmethod
from collections.abc import Callable

class UncaughtExceptionHandler(Callable[[Exception, bool], None], ABC):
    @abstractmethod
    def handle_uncaught_exception(self, throwable: Exception, do_shut_down: bool) -> None:
        pass
    
    def __call__(self, throwable: Exception, do_shut_down: bool) -> None:
        self.handle_uncaught_exception(throwable, do_shut_down)
