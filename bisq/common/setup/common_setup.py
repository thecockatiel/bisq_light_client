from collections.abc import Callable
import contextvars
from datetime import timedelta
import platform
import sys
import traceback
import threading
from types import TracebackType
from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
from signal import signal, SIGINT, SIGTERM

from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.common.user_thread import UserThread
from bisq.common.util.profiler import Profiler
from bisq.common.version import Version
from twisted.python import log

if TYPE_CHECKING:
    from bisq.common.config.config import Config


class CommonSetup:
    @staticmethod
    def setup_sig_int_handlers(graceful_shut_down_handler: GracefulShutDownHandler):
        shutdown_initiated = False
        logger = get_ctx_logger(__name__)

        def signal_handler(sig: int, frame):
            nonlocal shutdown_initiated
            if shutdown_initiated:
                logger.info(f"Shutdown in progress")
                return
            shutdown_initiated = True
            logger.info(f"Received signal {sig}")
            UserThread.execute(
                lambda: graceful_shut_down_handler.graceful_shut_down(lambda *_: None)
            )

        if platform.system() == "Windows":
            try:
                signal(SIGINT, signal_handler)
                signal(SIGTERM, signal_handler)
            except Exception as e:
                logger.warning(
                    f"Could not set up signal handlers on windows: {e}"
                )

            if threading.current_thread() is threading.main_thread():
                # Add keyboard interrupt handler as fallback
                def keyboard_interrupt_handler():
                    while True:
                        try:
                            input()
                        except (KeyboardInterrupt, EOFError):
                            UserThread.execute(
                                lambda: graceful_shut_down_handler.graceful_shut_down(
                                    lambda *_: None
                                )
                            )
                            break
                ctx = contextvars.copy_context()
                keyboard_thread = threading.Thread(
                    target=ctx.run,
                    args=(keyboard_interrupt_handler,),
                    daemon=True,
                    name="KeyboardInterruptHandlerThread",
                )
                keyboard_thread.start()
        else:
            # Unix-like systems
            signal(SIGINT, signal_handler)
            signal(SIGTERM, signal_handler)

    @staticmethod
    def setup_uncaught_exception_handler(
        uncaught_exception_handler: UncaughtExceptionHandler,
    ):
        original_excepthook = sys.excepthook
        logger = get_ctx_logger(__name__)

        def exception_handler(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType,
            thread: threading.Thread = None,
        ):
            if exc_type.__name__ == "SystemExit":
                original_excepthook(exc_type, exc_value, exc_traceback)
                return

            if exc_type.__name__ in [
                "CancelledError",
                "AsyncioCancelledError",
                "BrokenPipeError",
                "ConnectionResetError",
            ]:
                return

            if isinstance(exc_value, MemoryError):
                logger.error(
                    "OutOfMemoryError occurred. We shut down.",
                    exc_info=(exc_type, exc_value, exc_traceback),
                )
                UserThread.execute(
                    lambda: uncaught_exception_handler.handle_uncaught_exception(
                        exc_value, True
                    )
                )
            else:
                logger.error(
                    f"Uncaught Exception from thread {threading.current_thread().name}"
                )
                logger.error(f"throwableMessage= {str(exc_value)}")
                logger.error(f"throwableClass= {exc_type.__name__}")
                (
                    logger.error(
                        f"Stack trace:\n{''.join(traceback.format_tb(exc_traceback))}"
                    )
                    if exc_traceback
                    else None
                )
                should_exit = exc_type.__name__ == "ImportError"
                UserThread.execute(
                    lambda: uncaught_exception_handler.handle_uncaught_exception(
                        exc_value, should_exit
                    )
                )

        sys.excepthook = exception_handler
        threading.excepthook = lambda args: exception_handler(
            args.exc_type, args.exc_value, args.exc_traceback, args.thread
        )

        def on_twisted_log(event: dict):
            if event["isError"] and event["failure"]:
                failure = event["failure"]
                exception = failure.value
                if (
                    isinstance(exception, (RuntimeError))
                    and str(failure.value) == "Tor exited with error-code 0"
                ):
                    return  # Ignore this error
                exception_handler(
                    type(exception), exception, failure.getTracebackObject()
                )

        log.startLoggingWithObserver(on_twisted_log, 0)

    @staticmethod
    def setup(config: "Config", graceful_shut_down_handler: GracefulShutDownHandler):
        Version.set_base_crypto_network_id(config.base_currency_network.value)
        Version.print_version()
        Profiler.print_system_load()
        CommonSetup.setup_sig_int_handlers(graceful_shut_down_handler)
        DevEnv.setup(config)

    @staticmethod
    def start_periodic_tasks():
        Profiler.print_system_load_periodically(timedelta(minutes=10))

    @staticmethod
    def _get_version_file(config: "Config"):
        return config.app_data_dir.joinpath("version")

    @staticmethod
    def persist_bisq_version(config: "Config"):
        version_file = CommonSetup._get_version_file(config)
        try:
            with version_file.open("w") as file_writer:
                file_writer.write(Version.VERSION)
        except Exception as e:
            logger = get_ctx_logger(__name__)
            logger.error(f"Writing Version failed. {e}", exc_info=e)

    @staticmethod
    def get_last_bisq_version(config: "Config") -> Optional[str]:
        version_file = CommonSetup._get_version_file(config)
        if not version_file.exists():
            return None
        try:
            with version_file.open() as f:
                # We only expect 1 line
                return f.readline().strip()
        except Exception as e:
            logger = get_ctx_logger(__name__)
            logger.error(e)
        return None

    @staticmethod
    def is_downgrade(last_version: str):
        return bool(last_version and Version.is_new_version(last_version, Version.VERSION))

    @staticmethod
    def has_downgraded(
        config: "Config",
        down_grade_prevention_handler: Optional[Callable[[str], None]] = None,
    ) -> bool:
        last_version = CommonSetup.get_last_bisq_version(config)
        has_downgraded = CommonSetup.is_downgrade(last_version)
        if has_downgraded:
            logger = get_ctx_logger(__name__)
            logger.error(
                f"Downgrade from version {last_version} to version {Version.VERSION} is not supported"
            )
            if down_grade_prevention_handler is not None:
                down_grade_prevention_handler(last_version)
        return has_downgraded
