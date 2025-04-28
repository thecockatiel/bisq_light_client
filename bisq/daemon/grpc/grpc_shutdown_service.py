from datetime import timedelta
from typing import TYPE_CHECKING
from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.user_thread import UserThread
from grpc_pb2_grpc import ShutdownServerServicer
from grpc_pb2 import StopReply, StopRequest

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler


class GrpcShutdownService(ShutdownServerServicer):

    def __init__(
        self,
        exception_handler: "GrpcExceptionHandler",
        graceful_shut_down_handler: "GracefulShutDownHandler",
    ):
        self.logger = get_ctx_logger(__name__)
        self._exception_handler = exception_handler
        self._graceful_shut_down_handler = graceful_shut_down_handler

    def Stop(self, request: "StopRequest", context: "ServicerContext"):
        try:
            self.logger.info("Shutdown request received.")
            reply = StopReply()
            UserThread.run_after(
                self._graceful_shut_down_handler.graceful_shut_down,
                timedelta(milliseconds=500),
            )
            return reply
        except Exception as e:
            self._exception_handler.handle_exception(self.logger, e, context)
