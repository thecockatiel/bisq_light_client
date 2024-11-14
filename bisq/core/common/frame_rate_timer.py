import uuid
from collections.abc import Callable
from datetime import timedelta

from bisq.core.common.master_timer import MasterTimer
from bisq.logging import get_logger
from utils.time import get_time_ms
from .timer import Timer

logger = get_logger(__name__)

class FrameRateTimer(Timer, Callable[[], None]):
    """
    We simulate a global frame rate timer similar to FXTimer to avoid creation of threads for each timer call.
    Used only in headless apps like the seed node.
    """
    def __init__(self):
        self._interval = 0
        self._callable: Callable[[], None] = None
        self._start_ts = 0
        self._is_periodically = False
        self._uid = str(uuid.uuid4())
        self._stopped = False
        MasterTimer.add_listener(self)

    def __call__(self, *args, **kwargs):
        if not self._stopped:
            try:
                current_time = get_time_ms()
                if (current_time - self._start_ts) >= self._interval:
                    self._callable()
                    if self._is_periodically:
                        self._start_ts = current_time
                    else:
                        self.stop()
            except Exception as e:
                logger.error("exception in FrameRateTimer", exc_info=e)
                self.stop()
                raise

    def run_later(self, delay: timedelta, callable: Callable[[], None]):
        self._interval = int(delay.total_seconds() * 1000)
        self._callable = callable
        self._start_ts = get_time_ms()
        MasterTimer.add_listener(self)
        return self

    def run_periodically(self, interval: timedelta, callable: Callable[[], None]):
        self._interval = int(interval.total_seconds() * 1000)
        self._is_periodically = True
        self._callable = callable
        self._start_ts = get_time_ms()
        MasterTimer.add_listener(self)
        return self

    def stop(self):
        self._stopped = True
        MasterTimer.remove_listener(self)

    def __eq__(self, other):
        if isinstance(other, FrameRateTimer):
            return self._uid and self._uid == other._uid
        return False

    def __hash__(self) -> int:
        return hash(self._uid) if self._uid else 0