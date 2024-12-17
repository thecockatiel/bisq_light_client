
from abc import ABC, abstractmethod


class ClockWatcherListener(ABC):
    @abstractmethod
    def on_second_tick(self) -> None:
        pass

    @abstractmethod
    def on_minute_tick(self) -> None:
        pass

    def on_missed_second_tick(self, missed_ms: int) -> None:
        pass

    def on_awake_from_standby(self, missed_ms: int) -> None:
        pass