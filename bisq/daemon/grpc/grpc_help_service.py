from typing import TYPE_CHECKING
from bisq.core.user.user_manager import UserManager
from grpc_pb2_grpc import HelpServicer
from grpc_pb2 import GetMethodHelpRequest, GetMethodHelpReply

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi


class GrpcHelpService(HelpServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def GetMethodHelp(
        self, request: "GetMethodHelpRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            return GetMethodHelpReply(
                method_help=self._core_api.get_method_help(request.method_name)
            )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)
