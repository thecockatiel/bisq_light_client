from abc import ABC, abstractmethod
from datetime import timedelta
from collections.abc import Callable

class Timer(ABC):

    @abstractmethod
    def run_later(self, delay: timedelta, action: Callable[[], None]) -> 'Timer':
        pass

    @abstractmethod
    def run_periodically(self, interval: timedelta, runnable: Callable[[], None]) -> 'Timer':
        pass

    @abstractmethod
    def stop(self) -> None:
        pass