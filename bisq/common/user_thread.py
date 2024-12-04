from datetime import timedelta
import random
from collections.abc import Callable
from bisq.common.timer import Timer
from bisq.common.setup.log_setup import get_logger
from bisq.common.twisted_timer import TwistedTimer
 
logger = get_logger(__name__)

class UserThread:
    """
    Defines which thread is used as user thread. The user thread is the main thread in the single-threaded context.
    For GUI applications, it is usually the main thread, otherwise it can be any single-threaded executor.
    Additionally sets a timer class so different timers can be used based on the application context.
    
    Provides also methods for delayed and periodic executions.
    """
    timer_class: Timer = TwistedTimer

    @classmethod
    def set_timer_class(cls, timer_class: Timer):
        cls.timer_class = timer_class

    @classmethod
    def execute(cls, runnable: Callable[[], None]):
        cls.run_after(runnable, timedelta(microseconds=0))

    @classmethod
    def run_after_random_delay(cls, runnable: Callable[[], None], min_delay: timedelta, max_delay: timedelta) -> Timer:
        delay = random.uniform(min_delay.total_seconds(), max_delay.total_seconds())
        return cls.run_after(runnable, timedelta(seconds=delay))

    @classmethod
    def run_after(cls, runnable: Callable[[], None], delay: timedelta) -> Timer:
        return cls.get_timer().run_later(delay, runnable)

    @classmethod
    def run_periodically(cls, runnable: Callable[[], None], interval: timedelta) -> Timer:
        return cls.get_timer().run_periodically(interval, runnable)

    @classmethod
    def get_timer(cls) -> Timer:
        try:
            return cls.timer_class()
        except Exception as e:
            message = f"Could not instantiate timer_class={cls.timer_class}"
            logger.error(message, exc_info=e)
            raise RuntimeError(message) from e