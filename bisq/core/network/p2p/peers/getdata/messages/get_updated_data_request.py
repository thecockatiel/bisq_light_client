from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.network.p2p.peers.getdata.messages.get_data_request import GetDataRequest
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
import pb_pb2 as protobuf
from utils.data import raise_required

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.node_address import NodeAddress



@dataclass
class GetUpdatedDataRequest(GetDataRequest, SendersNodeAddressMessage):
    sender_node_address: "NodeAddress" = field(default_factory=raise_required)

    def __post_init__(self):
        self.logger = get_ctx_logger(__name__)

    def to_proto_network_envelope(self) -> "NetworkEnvelope":
        get_updated_data_request = protobuf.GetUpdatedDataRequest(
            sender_node_address=self.sender_node_address.to_proto_message(),
            nonce=self.nonce,
            excluded_keys=self.excluded_keys,
            version=self.version,
        )
        envelope = self.get_network_envelope_builder()
        envelope.get_updated_data_request.CopyFrom(get_updated_data_request)
        self.logger.info(
            f"Sending a GetUpdatedDataRequest with {envelope.ByteSize() / 1000} kB and "
            f"{len(self.excluded_keys)} excluded key entries. Requester's version={self.version}"
        )
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.GetUpdatedDataRequest, message_version: int
    ) -> "GetUpdatedDataRequest":
        excluded_keys = ProtoUtil.byte_set_from_proto_byte_string_list(
            proto.excluded_keys
        )
        requesters_version = ProtoUtil.string_or_none_from_proto(proto.version)
        logger = get_ctx_logger(__name__)
        logger.info(
            f"Received a GetUpdatedDataRequest with {proto.ByteSize() / 1000} kB and "
            f"{len(excluded_keys)} excluded key entries. Requester's version={requesters_version}"
        )

        return GetUpdatedDataRequest(
            message_version=message_version,
            nonce=proto.nonce,
            excluded_keys=excluded_keys,
            version=requesters_version,
            sender_node_address=NodeAddress.from_proto(proto.sender_node_address),
        )
