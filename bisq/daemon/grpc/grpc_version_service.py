from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import logger_context
from grpc_pb2_grpc import GetVersionServicer
from grpc_pb2 import GetVersionRequest, GetVersionReply

if TYPE_CHECKING:
    from bisq.core.user.user_manager import UserManager
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi


class GrpcVersionService(GetVersionServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def GetVersion(self, request: "GetVersionRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                return GetVersionReply(version=self._core_api.get_version())
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)
