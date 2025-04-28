from concurrent.futures import Future
import threading
from typing import TYPE_CHECKING
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import logger_context
from bisq.core.network.p2p.node_address import NodeAddress
from grpc_extra_pb2_grpc import DevCommandsServicer
from grpc_extra_pb2 import SendProtoRequest, SendProtoReply
from utils.aio import FutureCallback

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi
    from bisq.core.user.user_manager import UserManager


class GrpcDevCommandsService(DevCommandsServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self.core_api = core_api
        self.exception_handler = exception_handler
        self._user_manager = user_manager

    def SendProto(self, request: "SendProtoRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                class MyNetworkEnvelope(NetworkEnvelope):
                    def to_proto_message(self):
                        return request.network_envelope

                    def to_proto_network_envelope(self):
                        return request.network_envelope

                    def get_network_envelope_builder(self):
                        return request.network_envelope

                wrapped_envelope = MyNetworkEnvelope(
                    message_version=request.network_envelope.message_version
                )
                event = threading.Event()
                error = None

                f = self.core_api.send_network_envelope(
                    user_context,
                    NodeAddress.from_proto(request.destination_node_address),
                    wrapped_envelope,
                )

                def on_failure(e):
                    nonlocal error
                    error = e
                    event.set()

                f.add_done_callback(FutureCallback(lambda: event.set(), on_failure))
                event.wait()
                return (
                    SendProtoReply(success=False, error_message=str(error))
                    if error is not None
                    else SendProtoReply(success=True)
                )
        except Exception as e:
            self.exception_handler.handle_exception(user_context.logger, e, context)
