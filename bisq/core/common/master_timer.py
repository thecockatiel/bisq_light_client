import threading
import logging
import time
from typing import Callable, Set

# Runs all listener objects periodically in a short interval.
class MasterTimer:
    log = logging.getLogger('MasterTimer')
    FRAME_INTERVAL_MS = 100  # frame rate of 60 fps is about 16 ms but we don't need such a short interval, 100 ms should be good enough

    listeners: Set[Callable] = set()
    listeners_lock = threading.Lock()

    @staticmethod
    def start_timer():
        def run_timer():
            while True:
                MasterTimer.log.debug("Executing listeners")
                with MasterTimer.listeners_lock:
                    for listener in MasterTimer.listeners:
                        try:
                            listener()
                        except Exception as e:
                            MasterTimer.log.error(f"Error executing listener: {e}")
                time.sleep(MasterTimer.FRAME_INTERVAL_MS / 1000.0)

        timer_thread = threading.Thread(target=run_timer, daemon=True)
        timer_thread.start()

    @staticmethod
    def add_listener(runnable: Callable):
        with MasterTimer.listeners_lock:
            MasterTimer.listeners.add(runnable)
            MasterTimer.log.debug(f"Listener added: {runnable}")

    @staticmethod
    def remove_listener(runnable: Callable):
        with MasterTimer.listeners_lock:
            MasterTimer.listeners.discard(runnable)
            MasterTimer.log.debug(f"Listener removed: {runnable}")

# Initialize and start the timer
MasterTimer.start_timer()