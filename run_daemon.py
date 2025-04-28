#!/usr/bin/env python3
# -*- mode: python -*-
from utils.common_checks import do_common_checks

do_common_checks()


from utils.aio import as_future  # to install reactor first
import asyncio
from twisted.internet import reactor
from bisq.daemon.bisq_daemon_main import BisqDaemonMain

if __name__ == "__main__":
    daemon = BisqDaemonMain()
    future = as_future(daemon.main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()
