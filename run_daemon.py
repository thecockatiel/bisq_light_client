#!/usr/bin/env python3
# -*- mode: python -*-
import sys

from utils.pb_helper import check_and_use_pure_python_pb_implementation

check_and_use_pure_python_pb_implementation()

MIN_PYTHON_VERSION = "3.9.0"
_min_python_version_tuple = tuple(map(int, (MIN_PYTHON_VERSION.split("."))))


if sys.version_info[:3] < _min_python_version_tuple:
    sys.exit(
        f"Error: Bisq light client requires Python version >= {MIN_PYTHON_VERSION}..."
    )

import utils.aio  # to install reactor first
import asyncio
from twisted.internet import reactor
from bisq.daemon.bisq_daemon_main import BisqDaemonMain

if __name__ == "__main__":
    future = asyncio.ensure_future(BisqDaemonMain.main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()
