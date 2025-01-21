from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.app.bisq_executable import BisqExecutable
from bisq.common.version import Version
from bisq.core.app.bisq_headless_app import BisqHeadlessApp

if TYPE_CHECKING:
    from bisq.core.payment.trade_limits import TradeLimits

logger = get_logger(__name__)


class BisqHeadlessAppMain(BisqExecutable):

    def __init__(self):
        super().__init__("Bisq Light Daemon", "bisqd", "bisq_light_client", Version.VERSION)
        self.headless_app: "BisqHeadlessApp" = None
        self.trade_limits: "TradeLimits" = None

    def do_execute(self):
        super().do_execute()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // First synchronous execution tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def config_user_thread(self):
        pass  # no need in our implementation

    def launch_application(self):
        self.headless_app = BisqHeadlessApp()
        UserThread.execute(self.on_application_launched)

    def on_application_launched(self):
        super().on_application_launched()
        self.headless_app.graceful_shut_down_handler = self

    def handle_uncaught_exception(self, exception: Exception, do_shut_down: bool):
        return self.headless_app.handle_uncaught_exception(exception, do_shut_down)

    def on_setup_complete(self):
        logger.info("onSetupComplete")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // We continue with a series of synchronous execution tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def init_core_module(self):
        pass
    
    def apply_injector(self):
        super().apply_injector()
        self.headless_app.injector = self._injector

    def start_application(self):
        self.trade_limits = self._injector.trade_limits

        self.headless_app.start_application()

        self.on_application_started()
