from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import logger_context
from grpc_pb2_grpc import DisputeAgentsServicer
from grpc_pb2 import RegisterDisputeAgentRequest, RegisterDisputeAgentReply

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi
    from bisq.core.user.user_manager import UserManager


class GrpcDisputeAgentsService(DisputeAgentsServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self.core_api = core_api
        self.exception_handler = exception_handler
        self._user_manager = user_manager

    def RegisterDisputeAgent(
        self, request: "RegisterDisputeAgentRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self.core_api.register_dispute_agent(
                    user_context,
                    request.dispute_agent_type,
                    request.registration_key,
                )
                return RegisterDisputeAgentReply()
        except Exception as e:
            self.exception_handler.handle_exception(user_context.logger, e, context)

    # rateMeteringInterceptor implementation was skipped for not having a clear reason on why it was implemented
