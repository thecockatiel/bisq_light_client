#!/usr/bin/env python3
# -*- mode: python -*-
from utils.common_checks import do_common_checks

do_common_checks()


import utils.aio  # to install reactor first
import asyncio
from twisted.internet import reactor
from bisq.daemon.bisq_daemon_main import BisqDaemonMain

if __name__ == "__main__":
    future = asyncio.ensure_future(BisqDaemonMain.main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()
