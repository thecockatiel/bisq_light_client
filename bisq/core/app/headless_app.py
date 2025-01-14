from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.core.app.bisq_setup_listener import BisqSetupListener

if TYPE_CHECKING:
    from global_container import GlobalContainer
    from bisq.common.setup.graceful_shutdown_handler import GracefulShutDownHandler

# Keeping the name injector is intentional. we may replace global container with an actual injector in the future

class HeadlessApp(UncaughtExceptionHandler, BisqSetupListener, ABC):

    @property
    @abstractmethod
    def graceful_shutdown_handler(self) -> "GracefulShutDownHandler":
        pass

    @graceful_shutdown_handler.setter
    @abstractmethod
    def graceful_shutdown_handler(self, value: "GracefulShutDownHandler"):
        pass
    
    @property
    @abstractmethod
    def injector(self) -> "GlobalContainer":
        pass
    
    @injector.setter
    @abstractmethod
    def injector(self, injector: "GlobalContainer"):
        pass

    @abstractmethod
    def start_application(self):
        pass
