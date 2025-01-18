from utils.aio import as_deferred, as_future  # at top to prevent reactor problems
from functools import wraps
from twisted.internet import reactor, defer

def cancel_delayed_calls():
    for delayed_call in reactor.getDelayedCalls():
        delayed_call.cancel()


def twisted_wait(seconds: float):
    d = defer.Deferred()
    reactor.callLater(seconds, d.callback, True)
    return as_future(d)

def wrap_with_ensure_deferred(f):
    
    @wraps(f)
    def wrapper(*args, **kwargs):
        return as_deferred(f(*args, **kwargs))
    
    return wrapper
