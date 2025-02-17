from utils.aio import as_future
import asyncio
from typing import TYPE_CHECKING, Optional
from bisq.common.user_thread import UserThread
from bisq.core.app.bisq_headless_app_main import BisqHeadlessAppMain
from bisq.core.app.bisq_setup_listener import BisqSetupListener
from bisq.daemon.bisq_daemon import BisqDaemon
from twisted.internet.defer import Deferred

if TYPE_CHECKING:
    from bisq.daemon.grpc.grpc_server import GrpcServer


class BisqDaemonMain(BisqHeadlessAppMain, BisqSetupListener):

    def __init__(self):
        super().__init__()
        self._grpc_server: Optional["GrpcServer"] = None

    @staticmethod
    async def main():
        # entry point
        try:
            BisqDaemonMain().execute()
        except Exception as e:
            print(f"Unrecoverable Error: {e}")
        else:
            await BisqDaemonMain.keep_running()

    # /////////////////////////////////////////////////////////////////////////////////////
    # // First synchronous execution tasks
    # /////////////////////////////////////////////////////////////////////////////////////

    def config_user_thread(self):
        pass  # no need

    def launch_application(self):
        self.headless_app = BisqDaemon()
        self.headless_app.graceful_shut_down_handler = self
        UserThread.execute(self.on_application_launched)

    def on_application_launched(self):
        super().on_application_launched()

    # /////////////////////////////////////////////////////////////////////////////////////
    # // We continue with a series of synchronous execution tasks
    # /////////////////////////////////////////////////////////////////////////////////////

    def apply_injector(self):
        super().apply_injector()
        self.headless_app.injector = self._injector

    def start_application(self):
        super().start_application()

    def on_application_started(self):
        super().on_application_started()

        self._grpc_server = self._injector.grpc_server
        self._grpc_server.start()

    def graceful_shut_down(self, result_handler):
        BisqDaemonMain.stop_keep_running()
        super().graceful_shut_down(result_handler)

        if self._grpc_server:
            self._grpc_server.shut_down()


    _keep_running_future: "asyncio.Future" = None
    @staticmethod
    async def keep_running():
        while True:
            try:
                BisqDaemonMain._keep_running_future = as_future(Deferred())
                await BisqDaemonMain._keep_running_future
            except Exception as e:
                if isinstance(e, asyncio.CancelledError):
                    return
                # ignore other interruptions
    
    @staticmethod
    def stop_keep_running():
        if BisqDaemonMain._keep_running_future:
            BisqDaemonMain._keep_running_future.cancel()
            BisqDaemonMain._keep_running_future = None
