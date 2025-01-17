from typing import TYPE_CHECKING
from utils.aio import as_future
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.app.bisq_executable import BisqExecutable
import bisq.common.version as Version
from bisq.core.app.bisq_headless_app import BisqHeadlessApp
from twisted.internet.defer import Deferred

if TYPE_CHECKING:
    from bisq.core.payment.trade_limits import TradeLimits

logger = get_logger(__name__)


class BisqHeadlessAppMain(BisqExecutable):

    def __init__(self):
        super().__init__("Bisq Light Daemon", "bisq_light_client", Version.VERSION)
        self.headless_app: "BisqHeadlessApp" = None
        self.trade_limits: "TradeLimits" = None

    @staticmethod
    async def main():
        BisqHeadlessAppMain().execute()
        await BisqHeadlessAppMain.keep_running()

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
        self.headless_app.graceful_shutdown_handler = self

    def handle_uncaught_exception(self, exception: Exception, do_shut_down: bool):
        return self.headless_app.handle_uncaught_exception(exception, do_shut_down)

    def on_setup_complete(self):
        logger.info("onSetupComplete")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // We continue with a series of synchronous execution tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def apply_injector(self):
        super().apply_injector()
        self.headless_app.injector = self._injector

    def start_application(self):
        self.trade_limits = self._injector.trade_limits

        self.headless_app.start_application()

        self.on_application_started()

    async def keep_running(self):
        while True:
            try:
                await as_future(Deferred())
            except:
                # ignore interruptions
                pass
