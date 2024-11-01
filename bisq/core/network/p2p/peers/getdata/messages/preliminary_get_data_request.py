from dataclasses import dataclass
from typing import Optional

from bisq.core.common.capabilities import Capabilities
from bisq.core.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.anonymous_message import AnonymousMessage
from bisq.core.network.p2p.peers.getdata.messages.get_data_request import GetDataRequest
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.logging import get_logger

import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf

logger = get_logger(__name__)

@dataclass(frozen=True)
class PreliminaryGetDataRequest(GetDataRequest, AnonymousMessage, SupportedCapabilitiesMessage):
    supported_capabilities: Capabilities

    def __init__(self, nonce, excluded_keys, version: Optional[str] = Version.VERSION, supported_capabilities=Capabilities.app, message_version: int = Version.get_p2p_message_version()):
        super().__init__(message_version, nonce, excluded_keys, version)
        self.supported_capabilities = supported_capabilities

    def to_proto_network_envelope(self):
        request = protobuf.PreliminaryGetDataRequest()
        request.nonce = self.nonce
        request.excluded_keys.extend(self.excluded_keys)
        if self.version:
            request.version = self.version
        request.supported_capabilities.extend(self.supported_capabilities)
        envelope = self.get_network_envelope_builder()
        envelope.preliminary_get_data_request = request
        logger.info(f"Sending a PreliminaryGetDataRequest with {request.ByteSize() / 1000} kB and {len(self.excluded_keys)} excluded key entries. Requester's version={self.version}")
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.PreliminaryGetDataRequest, message_version: int):
        excluded_keys = ProtoUtil.byte_set_from_proto_byte_string_list(proto.excluded_keys)
        requesters_version  = ProtoUtil.string_or_null_from_proto(proto.version)
        supported_capabilities = Capabilities.from_int_list(proto.supported_capabilities)
        logger.info(f"Received a PreliminaryGetDataRequest with {proto.ByteSize() / 1000} kB and {len(excluded_keys)} excluded key entries. Requester's version={requesters_version}")
        return PreliminaryGetDataRequest(
            nonce=proto.nonce,
            excluded_keys=excluded_keys,
            version=requesters_version,
            supported_capabilities=supported_capabilities,
            message_version=message_version
        )