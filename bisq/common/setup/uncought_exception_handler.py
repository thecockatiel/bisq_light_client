from abc import ABC, abstractmethod

class UncaughtExceptionHandler(ABC):
    @abstractmethod
    def handle_uncaught_exception(self, throwable: Exception, do_shut_down: bool) -> None:
        pass
