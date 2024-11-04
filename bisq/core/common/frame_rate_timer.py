import uuid 
import time
from typing import Callable
from datetime import timedelta

from bisq.core.common.master_timer import MasterTimer
from bisq.logging import get_logger
from utils.time import get_time_ms
from .timer import Timer

logger = get_logger(__name__)

class FrameRateTimer(Timer, Callable):
    """
    We simulate a global frame rate timer similar to FXTimer to avoid creation of threads for each timer call.
    Used only in headless apps like the seed node.
    """
    def __init__(self):
        self.interval = 0
        self.runnable: Callable = None
        self.start_ts = 0
        self.is_periodically = False
        self.uid = str(uuid.uuid4())
        self.stopped = False
        MasterTimer.add_listener(self)

    def __call__(self, *args, **kwargs):
        self.run()

    def run(self):
        if not self.stopped:
            try:
                current_time = get_time_ms()
                if (current_time - self.start_ts) >= self.interval:
                    self.runnable()
                    if self.is_periodically:
                        self.start_ts = current_time
                    else:
                        self.stop()
            except Exception as e:
                logger.error("exception in FrameRateTimer", exc_info=e)
                self.stop()
                raise

    def run_later(self, delay: timedelta, runnable: Callable):
        self.interval = int(delay.total_seconds() * 1000)
        self.runnable = runnable
        self.start_ts = get_time_ms()
        MasterTimer.add_listener(self)
        return self

    def run_periodically(self, interval: timedelta, runnable: Callable):
        self.interval = int(interval.total_seconds() * 1000)
        self.is_periodically = True
        self.runnable = runnable
        self.start_ts = get_time_ms()
        MasterTimer.add_listener(self)
        return self

    def stop(self):
        self.stopped = True
        MasterTimer.remove_listener(self)

    def __eq__(self, other):
        if isinstance(other, FrameRateTimer):
            return self.uid == other.uid
        return False

    def __hash__(self) -> int:
        return hash(self.uid)