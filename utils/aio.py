import asyncio
from collections.abc import Callable
from concurrent.futures import Future as ConcurrentFuture
from functools import partial
import inspect
import platform
import sys
import threading
from typing import Any, Awaitable, Optional, Tuple, Union, Coroutine, TypeVar
from twisted.internet.defer import Deferred
_T = TypeVar("T")
_R = TypeVar("R")


def _get_running_loop() -> Optional[asyncio.AbstractEventLoop]:
    """Returns the asyncio event loop that is *running in this thread*, if any."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None

AS_LIB_USER_I_WANT_TO_MANAGE_MY_OWN_ASYNCIO_LOOP = False
    
_asyncio_event_loop = None  # type: Optional[asyncio.AbstractEventLoop]
def get_asyncio_loop() -> asyncio.AbstractEventLoop:
    """Returns the global asyncio event loop we use."""
    if loop := _asyncio_event_loop:
        return loop
    if AS_LIB_USER_I_WANT_TO_MANAGE_MY_OWN_ASYNCIO_LOOP:
        if loop := _get_running_loop():
            return loop
    raise Exception("event loop not created yet")


def create_event_loop() -> Tuple[asyncio.AbstractEventLoop,
                                           asyncio.Future,
                                           threading.Thread]:
    global _asyncio_event_loop
    if _asyncio_event_loop is not None:
        raise Exception("there is already a running event loop")

    if platform.system().lower() == 'windows':
        asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy

    # asyncio.get_event_loop() became deprecated in python3.10. (see https://github.com/python/cpython/issues/83710)
    # We set a custom event loop policy purely to be compatible with code that
    # relies on asyncio.get_event_loop().
    # - in python 3.8-3.9, asyncio.Event.__init__, asyncio.Lock.__init__,
    #   and similar, calls get_event_loop. see https://github.com/python/cpython/pull/23420
    class MyEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
        def get_event_loop(self):
            # In case electrum is being used as a library, there might be other
            # event loops in use besides ours. To minimise interfering with those,
            # if there is a loop running in the current thread, return that:
            running_loop = _get_running_loop()
            if running_loop is not None:
                return running_loop
            # Otherwise, return our global loop:
            return get_asyncio_loop()
    asyncio.set_event_loop_policy(MyEventLoopPolicy())

    loop = asyncio.new_event_loop()
    _asyncio_event_loop = loop
    return loop


def as_future(d: Union[Deferred[_T], ConcurrentFuture[_T], Coroutine[Any,Any,_T]]) -> asyncio.Future[_T]:
    if isinstance(d, Deferred):
        return d.asFuture(get_asyncio_loop())
    if isinstance(d, ConcurrentFuture):
        return asyncio.wrap_future(d, loop=get_asyncio_loop())
    if asyncio.iscoroutine(d) or isinstance(d, asyncio.Future) or isinstance(d, asyncio.Task):
        return asyncio.ensure_future(d, loop=get_asyncio_loop())
    raise TypeError(f"unexpected type {type(d)}")


def as_deferred(f: Union[Coroutine, asyncio.Future[_T]]) -> Deferred[_T]:
    return Deferred.fromFuture(asyncio.ensure_future(f))

def is_async_callable(obj):
    """Check if an object is an async callable"""
    if hasattr(obj, '__call__'):
        # Check if it's a coroutine function
        if asyncio.iscoroutinefunction(obj):
            return True
        # Check if it's an async __call__ method
        if inspect.iscoroutinefunction(getattr(obj, '__call__')):
            return True
        # Handle partial functions
        if isinstance(obj, partial):
            return is_async_callable(obj.func)
    return False

async def run_in_thread(func: Callable[...,_T], *args: _R):
    '''Run a function in a separate thread, and await its completion.'''
    return await get_asyncio_loop().run_in_executor(None, func, *args)

def run_in_loop(coro: Awaitable[_T]) -> asyncio.Future[_T]:
    '''Run a function in current thread's asyncio loop and return a future'''
    concurrent_future = asyncio.run_coroutine_threadsafe(coro, get_asyncio_loop())
    return asyncio.wrap_future(concurrent_future, loop=get_asyncio_loop())

from twisted.internet import asyncioreactor
asyncioreactor.install(create_event_loop())

from twisted.internet import reactor
def stop_reactor_and_exit(status_code: int = 0):
    try:
        if reactor.running:
            reactor.stop()
    except:
        pass
    sys.exit(status_code)
