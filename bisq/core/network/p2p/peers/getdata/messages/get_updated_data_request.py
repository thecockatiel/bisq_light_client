from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Set
 
from bisq.core.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.peers.getdata.messages.get_data_request import GetDataRequest
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
from bisq.logging import get_logger
import proto.pb_pb2 as protobuf

import bisq.core.common.version as Version

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.node_address import NodeAddress

logger = get_logger(__name__)

@dataclass(frozen=True)
class GetUpdatedDataRequest(GetDataRequest, SendersNodeAddressMessage):
    sender_node_address: 'NodeAddress'

    def __init__(self, sender_node_address: NodeAddress, nonce: int, excluded_keys: Set[bytes],
                 version: Optional[str] = Version.VERSION, message_version: int = Version.get_p2p_message_version()):
        super().__init__(message_version, nonce, excluded_keys, version)
        self.sender_node_address = sender_node_address

    def to_proto_network_envelope(self) -> NetworkEnvelope:
        get_updated_data_request = protobuf.GetUpdatedDataRequest(
            sender_node_address=self.sender_node_address.to_proto_message(),
            nonce=self.nonce,
            excluded_keys=self.excluded_keys
        )
        if self.version:
            get_updated_data_request.version = self.version
        envelope = protobuf.NetworkEnvelope(
            get_updated_data_request=get_updated_data_request
        )
        logger.info(f"Sending a GetUpdatedDataRequest with {envelope.ByteSize() / 1000} kB and "
                     f"{len(self.excluded_keys)} excluded key entries. Requester's version={self.version}")
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.GetUpdatedDataRequest, message_version: int) -> 'GetUpdatedDataRequest':
        excluded_keys = ProtoUtil.byte_set_from_proto_byte_string_list(proto.excluded_keys)
        requesters_version = ProtoUtil.string_or_null_from_proto(proto.version)
        logger.info(f"Received a GetUpdatedDataRequest with {proto.ByteSize() / 1000} kB and "
                     f"{len(excluded_keys)} excluded key entries. Requester's version={requesters_version}")
        
        return GetUpdatedDataRequest(
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
            nonce=proto.nonce,
            excluded_keys=excluded_keys,
            version=requesters_version,
            message_version=message_version
        )