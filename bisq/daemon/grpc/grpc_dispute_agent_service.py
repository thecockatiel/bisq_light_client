from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from grpc_pb2_grpc import DisputeAgentsServicer
from grpc_pb2 import RegisterDisputeAgentRequest, RegisterDisputeAgentReply

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcDisputeAgentsService(DisputeAgentsServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        super().__init__()
        self.core_api = core_api
        self.exception_handler = exception_handler

    def RegisterDisputeAgent(
        self, request: "RegisterDisputeAgentRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.register_dispute_agent(
                request.dispute_agent_type, request.registration_key
            )
            return RegisterDisputeAgentReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    # rateMeteringInterceptor implementation was skipped for not having a clear reason on why it was implemented
