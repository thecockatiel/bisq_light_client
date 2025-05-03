import contextvars
import threading
import time
from collections.abc import Callable

from bisq.common.setup.log_setup import get_base_logger
from utils.concurrency import ThreadSafeSet

logger = get_base_logger(__name__)

# Runs all listener objects periodically in a short interval.
class MasterTimer:
    FRAME_INTERVAL_MS = 100  # frame rate of 60 fps is about 16 ms but we don't need such a short interval, 100 ms should be good enough

    listeners: ThreadSafeSet[Callable[[], None]] = ThreadSafeSet()
    _stop_flag = threading.Event()

    @staticmethod
    def start_timer():
        def run_timer():
            while not MasterTimer._stop_flag.is_set():
                logger.debug("Executing listeners")
                for callable in MasterTimer.listeners:
                    try:
                        callable()
                    except Exception as e:
                        MasterTimer.logger.error(f"Error executing listener: {e}")
                time.sleep(MasterTimer.FRAME_INTERVAL_MS / 1000.0)
        ctx = contextvars.copy_context()
        timer_thread = threading.Thread(target=ctx.run, args=(run_timer,), daemon=True, name="MasterTimerThread")
        timer_thread.start()

    @staticmethod
    def add_listener(runnable: Callable[[], None]):
        MasterTimer.listeners.add(runnable)
        logger.debug(f"Listener added: {runnable}")

    @staticmethod
    def remove_listener(runnable: Callable[[], None]):
        MasterTimer.listeners.discard(runnable)
        logger.debug(f"Listener removed: {runnable}")

    @staticmethod
    def shut_down():
        MasterTimer._stop_flag.set()
        MasterTimer.listeners.clear()


# Initialize and start the timer
MasterTimer.start_timer()