import utils.aio # IMPORTANT: this most be called before reactor is imported to properly install the asyncio event loop.
import uuid
from datetime import timedelta
from collections.abc import Callable
from twisted.internet import reactor
from twisted.internet.task import deferLater
from utils.time import get_time_ms
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer

logger = get_logger(__name__)

class TwistedTimer(Timer):
    """
    We simulate a global frame rate timer similar to FXTimer to avoid creation of threads for each timer call.
    Used only in headless apps like the seed node.
    """
    def __init__(self):
        self._callable: Callable[[], None] = None
        self._is_periodically = False
        self._uid = str(uuid.uuid4())
        self._stopped = False
        self._deferred = None

    def _run_later(self, delay: timedelta, callable: Callable[[], None]):
        self._is_periodically = False
        self._stopped = False
        self._callable = callable
        self._start_ts = get_time_ms()
        self._deferred = deferLater(reactor, delay.total_seconds(), self._callable)
        return self

    def run_later(self, delay: timedelta, callable: Callable[[], None]):
        reactor.callFromThread(self._run_later, delay, callable)
        return self

    def _run_periodically(self, interval: timedelta, callable: Callable[[], None]):
        self._is_periodically = True
        self._stopped = False
        self._callable = callable
        self._start_ts = get_time_ms()
        self._deferred = deferLater(reactor, interval.total_seconds(), self._callable)
        self._deferred.addBoth(lambda _: self._run_periodically(interval, callable))
        return self

    def run_periodically(self, interval: timedelta, callable: Callable[[], None]):
        reactor.callFromThread(self._run_periodically, interval, callable)
        return self

    def _stop(self):
        self._stopped = True
        self._deferred.cancel()

    def stop(self):
        reactor.callFromThread(self._stop)

    def __eq__(self, other):
        if isinstance(other, TwistedTimer):
            return self._uid and self._uid == other._uid
        return False

    def __hash__(self) -> int:
        return hash(self._uid) if self._uid else 0