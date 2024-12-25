#!/usr/bin/env python3
# -*- mode: python -*-

from collections.abc import Callable
from datetime import timedelta
import os
import sys
import threading

from utils.concurrency import AtomicInt

MIN_PYTHON_VERSION = "3.10.0"
_min_python_version_tuple = tuple(map(int, (MIN_PYTHON_VERSION.split("."))))


if sys.version_info[:3] < _min_python_version_tuple:
    sys.exit("Error: Bisq light client requires Python version >= %s..." % MIN_PYTHON_VERSION)

from bisq.core.setup.core_persisted_data_host import CorePersistedDataHost
from utils.aio import as_future, get_asyncio_loop
from global_container import GLOBAL_CONTAINER


import asyncio
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from bisq.common.setup.log_setup import configure_logging, get_logger

configure_logging(log_file=GLOBAL_CONTAINER.config.app_data_dir.joinpath("bisq.log"), log_level=GLOBAL_CONTAINER.config.log_level)

logger = get_logger(__name__)

from bisq.common.setup.common_setup import CommonSetup
from bisq.common.persistence.persistence_manager import PersistenceManager
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.graceful_shutdown_handler import GracefulShutDownHandler
from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.common.user_thread import UserThread
from bisq.core.setup.core_setup import CoreSetup

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
        self.is_shutdown_in_progress = False
        self.shutdown_requested = False
        self.has_downgraded = False

    async def execute(self):
        CommonSetup.setup_sig_int_handlers(self)
        CommonSetup.setup_uncaught_exception_handler(self)
        CommonSetup.setup(GLOBAL_CONTAINER.config, self)
        CoreSetup.setup()
        CommonSetup.start_periodic_tasks()
        ###############
        UserThread.run_after(self.step2, timedelta(milliseconds=1))
        await as_future(Deferred())
    
    def step2(self):
        self.read_maps_from_resources(self.step3)
        
    def step3(self):
        self.read_all_persisted(self.step4)
    
    def step4(self):
        PersistenceManager.on_all_services_initialized()
        asyncio.run_coroutine_threadsafe(GLOBAL_CONTAINER.p2p_service.start(), get_asyncio_loop())
    
    def graceful_shut_down(self, result_handler):
        logger.info("Shutting down gracefully")
        if self.is_shutdown_in_progress:
            return
        self.is_shutdown_in_progress = True
        
        def timeout_handler():
            logger.warning("Graceful shutdown not completed in 10 sec. We trigger our timeout handler.")
            self.flush_and_exit(result_handler, MainApp.EXIT_SUCCESS)

        UserThread.run_after(timeout_handler, timedelta(seconds=10))
        
        try:
            GLOBAL_CONTAINER.clock_watcher.shut_down()
            GLOBAL_CONTAINER.price_feed_service.shut_down()
            GLOBAL_CONTAINER.arbitrator_manager.shut_down()
        except Exception as e:
            logger.error("App shutdown failed with an exception", exc_info=e)
            self.flush_and_exit(result_handler, MainApp.EXIT_FAILURE)
            
    
    def flush_and_exit(self, result_handler: ResultHandler, status: int):
        def finish():
            reactor.stop()
            os._exit(status)
        if not self.has_downgraded:
            # If user tried to downgrade we do not write the persistable data to avoid data corruption
            logger.info("PersistenceManager flushAllDataToDiskAtShutdown started")
            def exit_sequence():
                logger.info("Graceful shutdown completed. Exiting now.")
                if result_handler:
                    result_handler()
                # Schedule system exit after 100ms
                UserThread.run_after(finish, timedelta(milliseconds=100))
            
            PersistenceManager.flush_all_data_to_disk_at_shutdown(exit_sequence)
        else:
            UserThread.run_after(finish, timedelta(milliseconds=100))

    def stop(self):
        if not self.shutdown_requested:
            UserThread.run_after(lambda: self.graceful_shut_down(lambda: logger.debug("App shutdown complete")), timedelta(milliseconds=200))
            self.shutdown_requested = True
    
    def handle_uncaught_exception(self, throwable, do_shut_down):
        if not self.shutdown_requested:
            logger.error(throwable)
            if do_shut_down:
                self.stop()
                
    def read_maps_from_resources(self, complete_handler: Callable):
        post_fix = "_" + GLOBAL_CONTAINER.config.base_currency_network.name.lower()
        GLOBAL_CONTAINER.p2p_data_storage.read_from_resources(post_fix, complete_handler)

    def read_all_persisted(self, complete_handler: Callable):
        hosts = CorePersistedDataHost.get_persisted_data_hosts(GLOBAL_CONTAINER)
        remaining = AtomicInt(len(hosts))
        for host in hosts:
            def on_read():
                if (remaining.decrement_and_get() == 0):
                    UserThread.execute(complete_handler)
            host.read_persisted(on_read)


if __name__ == '__main__':
    app = MainApp()
    future = asyncio.ensure_future(app.execute())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()