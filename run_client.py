#!/usr/bin/env python3
# -*- mode: python -*-

import sys

MIN_PYTHON_VERSION = "3.10.0"
_min_python_version_tuple = tuple(map(int, (MIN_PYTHON_VERSION.split("."))))


if sys.version_info[:3] < _min_python_version_tuple:
    sys.exit("Error: Bisq light client requires Python version >= %s..." % MIN_PYTHON_VERSION)


from utils.aio import as_future, create_event_loop
loop = create_event_loop()

from twisted.internet import asyncioreactor
asyncioreactor.install(loop)

import asyncio
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from bisq.log_setup import configure_logging

from utils.tor import setup_tor

async def main():
    configure_logging()
    socks_port = await setup_tor(reactor)
    print(f"Tor is running at: {socks_port}")
    await as_future(Deferred())


if __name__ == '__main__':
    future = asyncio.ensure_future(main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()