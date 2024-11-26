from datetime import timedelta
import sys
import traceback
import threading
from types import TracebackType
from bisq.common.app.dev_env import DevEnv
from bisq.common.config.config import CONFIG
from bisq.common.setup.log_setup import get_logger

from bisq.common.ascii_logo import show_ascii_logo
from bisq.common.setup.graceful_shutdown_handler import GracefulShutDownHandler
from signal import signal, SIGINT, SIGTERM

from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.common.user_thread import UserThread
from bisq.common.util.profiler import Profiler
import bisq.common.version as Version

logger = get_logger(__name__)

class CommonSetup:
    @staticmethod
    def setup_sig_int_handlers(graceful_shutdown_handler: GracefulShutDownHandler):
        def signal_handler(sig: int, frame):
            logger.info(f"Received signal {sig}")
            UserThread.execute(lambda: graceful_shutdown_handler(lambda: None))

        signal(SIGINT, signal_handler)
        signal(SIGTERM, signal_handler)

    @staticmethod
    def setup_uncaught_exception_handler(uncaught_exception_handler: UncaughtExceptionHandler):
        def exception_handler(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType, thread: threading.Thread = None):
            
            if isinstance(exc_value, MemoryError):
                logger.error("OutOfMemoryError occurred. We shut down.", exc_info=(exc_type, exc_value, exc_traceback))
                # Leave it to the handleUncaughtException to shut down or not.
                UserThread.execute(lambda: uncaught_exception_handler(exc_value, False))

            else:
                logger.error(f"Uncaught Exception from thread {threading.current_thread().name}")
                logger.error(f"throwableMessage= {str(exc_value)}")
                logger.error(f"throwableClass= {exc_type.__name__}")
                logger.error(f"Stack trace:\n{''.join(traceback.format_tb(exc_traceback))}")
                traceback.print_exc()
                UserThread.execute(lambda: uncaught_exception_handler(exc_value, False))

        sys.excepthook = exception_handler
        threading.excepthook = lambda args: exception_handler(args.exc_type, args.exc_value, args.exc_traceback, args.thread)

    @staticmethod
    def setup(graceful_shutdown_handler: GracefulShutDownHandler):
        # log is setup in log_setup when imported
        # config is also set up globally as CONFIG
        show_ascii_logo()
        Version.set_base_crypto_network_id(CONFIG.base_currency_network.value)
        Version.print_version()
        Profiler.print_system_load()
        CommonSetup.setup_sig_int_handlers(graceful_shutdown_handler)
        DevEnv.setup(CONFIG)

    @staticmethod
    def start_periodic_tasks():
        Profiler.print_system_load_periodically(timedelta(minutes=10))