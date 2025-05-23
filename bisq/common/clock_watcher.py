from datetime import timedelta
from typing import TYPE_CHECKING

from bisq.common.user_thread import UserThread
from bisq.common.setup.log_setup import get_base_logger
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.common.clock_watcher_listener import ClockWatcherListener
    from bisq.common.timer import Timer

logger = get_base_logger(__name__)


class ClockWatcher:
    """
    Helps configure listener objects that are run by the `UserThread` each second
    and can do per second, per minute and delayed second actions. Also detects when we were in standby, and logs it.
    """

    IDLE_TOLERANCE_MS = 20000

    def __init__(self):
        self._timer: "Timer" = None
        self._listeners: set["ClockWatcherListener"] = set()
        self._counter = 0
        self._last_second_tick = 0

    def start(self) -> None:
        if self._timer is None:
            self._last_second_tick = get_time_ms()
            self._timer = UserThread.run_periodically(
                self._on_timer, timedelta(seconds=1)
            )

    def _on_timer(self) -> None:
        """Handle timer tick events"""
        # Notify second listeners
        for listener in self._listeners:
            listener.on_second_tick()

        # Track minutes
        self._counter += 1
        if self._counter >= 60:
            self._counter = 0
            for listener in self._listeners:
                listener.on_minute_tick()

        # Check for missed time
        current_time_ms = get_time_ms()
        diff = current_time_ms - self._last_second_tick
        if diff > 1000:
            missed_ms = diff - 1000
            for listener in self._listeners:
                listener.on_missed_second_tick(missed_ms)

            if missed_ms > ClockWatcher.IDLE_TOLERANCE_MS:
                logger.info(f"We have been in standby mode for {missed_ms / 1000} sec")
                for listener in self._listeners:
                    listener.on_awake_from_standby(missed_ms)

        self._last_second_tick = current_time_ms

    def shut_down(self):
        if self._timer is not None:
            self._timer.stop()
        self._timer = None
        self._counter = 0

    def add_listener(self, listener: "ClockWatcherListener"):
        self._listeners.add(listener)

    def remove_listener(self, listener: "ClockWatcherListener"):
        self._listeners.discard(listener)
