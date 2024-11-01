from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import random
from typing import Callable, Type

from bisq.core.common.frame_rate_timer import FrameRateTimer
from .timer import Timer

from bisq.logging import get_logger
 
logger = get_logger(__name__)

class UserThread:
    """
    Defines which thread is used as user thread. The user thread is the main thread in the single-threaded context.
    For GUI applications, it is usually the main thread, otherwise it can be any single-threaded executor.
    Additionally sets a timer class so different timers can be used based on the application context.
    
    Provides also methods for delayed and periodic executions.
    """
    timer_class: Type[Timer] = FrameRateTimer
    executor = ThreadPoolExecutor(max_workers=1)

    @classmethod
    def set_timer_class(cls, timer_class: Type[Timer]):
        cls.timer_class = timer_class

    @classmethod
    def execute(cls, command: Callable):
        cls.executor.submit(command)

    @classmethod
    def run_after_random_delay(cls, runnable: Callable, min_delay_in_sec: int, max_delay_in_sec: int) -> Timer:
        delay = random.randint(min_delay_in_sec, max_delay_in_sec)
        return cls.run_after(runnable, delay)

    @classmethod
    def run_after(cls, runnable: Callable, delay: timedelta) -> Timer:
        return cls.get_timer().run_later(delay, runnable)

    @classmethod
    def run_periodically(cls, runnable: Callable, interval: timedelta) -> Timer:
        return cls.get_timer().run_periodically(interval, runnable)

    @classmethod
    def get_timer(cls) -> Timer:
        try:
            return cls.timer_class()
        except Exception as e:
            message = f"Could not instantiate timer_class={cls.timer_class}"
            logger.error(message, exc_info=e)
            raise RuntimeError(message) from e