from utils.aio import as_future  # to prevent reactor problems
from functools import wraps
from twisted.internet import reactor, defer
import asyncio


def run_with_reactor(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        error_container = []

        def handle_error(e: Exception):
            error_container.append(e)
            reactor.stop()

        def async_wrapper():
            try:
                future: asyncio.Future = asyncio.ensure_future(f(*args, **kwargs))

                def on_done(f: asyncio.Future):
                    try:
                        f.result()
                        reactor.stop()
                    except Exception as e:
                        handle_error(e)

                future.add_done_callback(on_done)
            except Exception as e:
                handle_error(e)

        reactor.callWhenRunning(async_wrapper)
        reactor.run()

        if error_container:
            raise error_container[0] from error_container[0]

    return wrapper


def teardown_reactor():
    for delayed_call in reactor.getDelayedCalls():
        delayed_call.cancel()


def twisted_wait(seconds: float):
    d = defer.Deferred()
    reactor.callLater(seconds, d.callback, True)
    return as_future(d)
