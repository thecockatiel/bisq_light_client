from concurrent.futures import Future
import threading
from typing import TYPE_CHECKING
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.daemon.grpc.grpc_waitable_callback_handler import GrpcWaitableCallbackHandler
from grpc_extra_pb2_grpc import DevCommandsServicer 
from grpc_extra_pb2 import SendProtoRequest, SendProtoReply 

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcDevCommandsService(DevCommandsServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def SendProto(self, request: "SendProtoRequest", context: "ServicerContext"):
        try:
            class MyNetworkEnvelope(NetworkEnvelope):            
                def to_proto_message(self):
                    return request.network_envelope
                def to_proto_network_envelope(self):
                    return request.network_envelope
                def get_network_envelope_builder(self):
                    return request.network_envelope
                
            wrapped_envelope = MyNetworkEnvelope(message_version=request.network_envelope.message_version)
            event = threading.Event()
            error = None
            def on_done(f: Future):
                nonlocal error
                try:
                    f.result()
                except Exception as e:
                    error = e
                event.set()

            f = self.core_api.send_network_envelope(NodeAddress.from_proto(request.destination_node_address), wrapped_envelope)
            f.add_done_callback(on_done)
            event.wait()
            return SendProtoReply(success=False, error_message=str(error)) if error is not None else SendProtoReply(success=True)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)