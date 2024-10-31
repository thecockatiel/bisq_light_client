from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Callable

class Timer(ABC):

    @abstractmethod
    def run_later(self, delay: timedelta, action: Callable) -> 'Timer':
        pass

    @abstractmethod
    def run_periodically(self, interval: timedelta, runnable: Callable) -> 'Timer':
        pass

    @abstractmethod
    def stop(self) -> None:
        pass