#!/usr/bin/env python3
# -*- mode: python -*-

from datetime import timedelta
import os
import sys
import threading

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

from bisq.common.setup.log_setup import configure_logging, get_logger

configure_logging()

logger = get_logger(__name__)

from bisq.common.setup.common_setup import CommonSetup
from bisq.common.persistence.persistence_manager import PersistenceManager
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.graceful_shutdown_handler import GracefulShutDownHandler
from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.common.user_thread import UserThread
from bisq.core.setup.core_setup import CoreSetup
from utils.tor import setup_tor

# TODO: check and implement
# This is a quick setup to test stuff. It should be replaced with proper setups based on the following files.
# https://github.com/bisq-network/bisq/blob/v1.9.17/core/src/main/java/bisq/core/app/BisqExecutable.java
# https://github.com/bisq-network/bisq/blob/v1.9.17/desktop/src/main/java/bisq/desktop/app/BisqAppMain.java
# https://github.com/bisq-network/bisq/blob/v1.9.17/desktop/src/main/java/bisq/desktop/app/BisqApp.java
# https://github.com/bisq-network/bisq/blob/v1.9.17/core/src/main/java/bisq/core/app/BisqHeadlessApp.java
# https://github.com/bisq-network/bisq/blob/v1.9.17/core/src/main/java/bisq/core/app/BisqSetup.java


# this is a messy setup to try stuff quickly with a lot of unsafe code for data. this needs to be replaced with proper setups.
class MainApp(GracefulShutDownHandler, UncaughtExceptionHandler):
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1
    
    def __init__(self) -> None:
        super().__init__()
        self.is_shutdown_in_progress = False
        self.shutdown_requested = False
        self.has_downgraded = False

    async def execute(self):
        CommonSetup.setup(self)
        CoreSetup.setup()
        CommonSetup.start_periodic_tasks()
        CommonSetup.setup_uncaught_exception_handler(self)

        socks_port = await setup_tor(reactor)
        print(f"Tor is running at: {socks_port}")
        await as_future(Deferred())
    
    def graceful_shut_down(self, result_handler):
        logger.info("Shutting down gracefully")
        if self.is_shutdown_in_progress:
            return
        self.is_shutdown_in_progress = True
        
        def timeout_handler():
            logger.warning("Graceful shutdown not completed in 10 sec. We trigger our timeout handler.")
            self.flush_and_exit(result_handler, MainApp.EXIT_SUCCESS)

        # We do not use the UserThread to avoid that the timeout would not get triggered in case the UserThread
        # would get blocked by a shutdown routine.
        shutdown_timer = threading.Timer(10.0, timeout_handler)
        shutdown_timer.start()
        
        
        try:
            # do proper service shutdowns
            raise Exception("Not implemented") # to end fast
        except Exception as e:
            logger.error("App shutdown failed with an exception", exc_info=e)
            self.flush_and_exit(result_handler, MainApp.EXIT_FAILURE)
            
    
    def flush_and_exit(self, result_handler: ResultHandler, status: int):
        if not self.has_downgraded:
            # If user tried to downgrade we do not write the persistable data to avoid data corruption
            logger.info("PersistenceManager flushAllDataToDiskAtShutdown started")
            def exit_sequence():
                logger.info("Graceful shutdown completed. Exiting now.")
                if result_handler:
                    result_handler()
                # Schedule system exit after 100ms
                UserThread.run_after(lambda: os._exit(status), timedelta(milliseconds=100))
            
            PersistenceManager.flush_all_data_to_disk_at_shutdown(exit_sequence)
        else:
            UserThread.run_after(lambda: os._exit(status), timedelta(milliseconds=100))

    def stop(self):
        if not self.shutdown_requested:
            UserThread.run_after(lambda: self.graceful_shut_down(lambda: logger.debug("App shutdown complete")), timedelta(milliseconds=200))
            self.shutdown_requested = True
    
    def handle_uncaught_exception(self, throwable, do_shut_down):
        if not self.shutdown_requested:
            logger.error(str(throwable))
            if do_shut_down:
                self.stop()


if __name__ == '__main__':
    app = MainApp()
    future = asyncio.ensure_future(app.execute())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()