from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from grpc_pb2_grpc import GetVersionServicer
from grpc_pb2 import GetVersionRequest, GetVersionReply

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcVersionService(GetVersionServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def GetMethodHelp(
        self, request: "GetVersionRequest", context: "ServicerContext"
    ):
        try:
            return GetVersionReply(
                version=self.core_api.get_version()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)
