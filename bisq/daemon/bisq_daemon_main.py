from typing import TYPE_CHECKING, Optional
from bisq.common.user_thread import UserThread
from bisq.core.app.bisq_headless_app_main import BisqHeadlessAppMain
from bisq.core.app.bisq_setup_listener import BisqSetupListener
from bisq.daemon.bisq_daemon import BisqDaemon

if TYPE_CHECKING:
    from bisq.daemon.grpc.grpc_server import GrpcServer


class BisqDaemonMain(BisqHeadlessAppMain, BisqSetupListener):

    def __init__(self):
        super().__init__()
        self._grpc_server: Optional["GrpcServer"] = None

    @staticmethod
    def main():
        # entry point
        BisqDaemonMain().execute()

    # /////////////////////////////////////////////////////////////////////////////////////
    # // First synchronous execution tasks
    # /////////////////////////////////////////////////////////////////////////////////////

    def config_user_thread(self):
        pass  # no need

    def launch_application(self):
        self.headless_app = BisqDaemon()
        UserThread.execute(self.on_application_launched)

    def on_application_launched(self):
        super().on_application_launched()
        self.headless_app.graceful_shutdown_handler = self

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
        super().graceful_shut_down(result_handler)

        self._grpc_server.shut_down()
