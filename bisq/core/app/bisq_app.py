from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bisq.core.app.bisq_setup_listener import BisqSetupListener

if TYPE_CHECKING:
    from bisq.core.user.user_context import UserContext
    from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
    from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler


class BisqApp(BisqSetupListener, ABC):

    def __init__(
        self,
        uncaught_exception_handler: "UncaughtExceptionHandler",
        graceful_shut_down_handler: "GracefulShutDownHandler",
        user_context: "UserContext",
    ):
        self._uncaught_exception_handler = uncaught_exception_handler
        self._graceful_shut_down_handler = graceful_shut_down_handler
        self._user_context = user_context
        self._logger = user_context.logger.getChild(__name__)
        self._corrupted_storage_file_handler = None
        self._trade_manager = None

    def start_user_instance(self):
        try:
            self._user_context.global_container.bisq_setup.add_bisq_setup_listener(self)
            self._corrupted_storage_file_handler = (
                self._user_context.global_container.corrupted_storage_file_handler
            )
            self._trade_manager = self._user_context.global_container.trade_manager

            self.setup_handlers()
            self._user_context.global_container.bisq_setup.start()
        except Exception as e:
            self._logger.error("Error during app init", exc_info=e)
            self._uncaught_exception_handler.handle_uncaught_exception(e, False)

    def shut_down(self):
        self._user_context.global_container.bisq_setup.remove_bisq_setup_listener(self)
        self._uncaught_exception_handler = None
        self._graceful_shut_down_handler = None
        self._user_context = None
        self._corrupted_storage_file_handler = None
        self._trade_manager = None

    @abstractmethod
    def setup_handlers(self):
        pass

    @abstractmethod
    def on_setup_complete(self):
        pass
