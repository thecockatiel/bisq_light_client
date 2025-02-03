from datetime import timedelta
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.app.bisq_headless_app import BisqHeadlessApp
from grpc_pb2_grpc import ShutdownServerServicer
from grpc_pb2 import StopReply, StopRequest

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcShutdownService(ShutdownServerServicer):

    def __init__(self, exception_handler: "GrpcExceptionHandler"):
        self.exception_handler = exception_handler

    def Stop(self, request: "StopRequest", context: "ServicerContext"):
        try:
            logger.info("Shutdown request received.")
            reply = StopReply()
            UserThread.run_after(
                BisqHeadlessApp.shut_down_handler, timedelta(milliseconds=500)
            )
            return reply
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)
