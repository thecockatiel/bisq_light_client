from dataclasses import dataclass, field

from bisq.common.capabilities import Capabilities
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.network.p2p.anonymous_message import AnonymousMessage
from bisq.core.network.p2p.peers.getdata.messages.get_data_request import GetDataRequest
from bisq.core.network.p2p.supported_capabilities_message import (
    SupportedCapabilitiesMessage,
)

import pb_pb2 as protobuf


@dataclass
class PreliminaryGetDataRequest(
    GetDataRequest, AnonymousMessage, SupportedCapabilitiesMessage
):
    supported_capabilities: Capabilities = field(
        default_factory=lambda: Capabilities.app
    )

    def __post_init__(self):
        self.logger = get_ctx_logger(__name__)

    def to_proto_network_envelope(self):
        request = protobuf.PreliminaryGetDataRequest(
            nonce=self.nonce,
            excluded_keys=self.excluded_keys,
            supported_capabilities=Capabilities.to_int_list(
                self.supported_capabilities
            ),
            version=self.version,
        )
        envelope = self.get_network_envelope_builder()
        envelope.preliminary_get_data_request.CopyFrom(request)
        self.logger.info(
            f"Sending a PreliminaryGetDataRequest with {request.ByteSize() / 1000} kB and {len(self.excluded_keys)} excluded key entries. Requester's version={self.version}"
        )
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.PreliminaryGetDataRequest, message_version: int):
        excluded_keys = ProtoUtil.byte_set_from_proto_byte_string_list(
            proto.excluded_keys
        )
        requesters_version = ProtoUtil.string_or_none_from_proto(proto.version)
        supported_capabilities = Capabilities.from_int_list(
            proto.supported_capabilities
        )
        logger = get_ctx_logger(__name__)
        logger.info(
            f"Received a PreliminaryGetDataRequest with {proto.ByteSize() / 1000} kB and {len(excluded_keys)} excluded key entries. Requester's version={requesters_version}"
        )
        return PreliminaryGetDataRequest(
            message_version=message_version,
            nonce=proto.nonce,
            excluded_keys=excluded_keys,
            version=requesters_version,
            supported_capabilities=supported_capabilities,
        )
