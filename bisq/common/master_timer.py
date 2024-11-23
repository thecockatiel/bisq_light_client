import threading
import time
from collections.abc import Callable

from bisq.common.setup.log_setup import get_logger
from utils.concurrency import ThreadSafeSet

logger = get_logger(__name__)

# Runs all listener objects periodically in a short interval.
class MasterTimer:
    FRAME_INTERVAL_MS = 100  # frame rate of 60 fps is about 16 ms but we don't need such a short interval, 100 ms should be good enough

    listeners: ThreadSafeSet[Callable[[], None]] = ThreadSafeSet()

    @staticmethod
    def start_timer():
        def run_timer():
            while True:
                logger.debug("Executing listeners")
                for callable in MasterTimer.listeners:
                    try:
                        callable()
                    except Exception as e:
                        MasterTimer.logger.error(f"Error executing listener: {e}")
                time.sleep(MasterTimer.FRAME_INTERVAL_MS / 1000.0)

        timer_thread = threading.Thread(target=run_timer, daemon=True)
        timer_thread.start()

    @staticmethod
    def add_listener(runnable: Callable[[], None]):
        MasterTimer.listeners.add(runnable)
        logger.debug(f"Listener added: {runnable}")

    @staticmethod
    def remove_listener(runnable: Callable[[], None]):
        MasterTimer.listeners.discard(runnable)
        logger.debug(f"Listener removed: {runnable}")

# Initialize and start the timer
MasterTimer.start_timer()