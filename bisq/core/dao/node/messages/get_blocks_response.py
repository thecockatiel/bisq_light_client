from typing import Optional
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.extended_data_size_permission import (
    ExtendedDataSizePermission,
)
from bisq.core.network.p2p.initial_data_response import InitialDataResponse
from bisq.core.dao.node.full.raw_block import RawBlock
import pb_pb2 as protobuf
from bisq.core.dao.node.messages.get_blocks_request import GetBlocksRequest


logger = get_logger(__name__)


class GetBlocksResponse(
    NetworkEnvelope, DirectMessage, ExtendedDataSizePermission, InitialDataResponse
):

    def __init__(
        self,
        blocks: list["RawBlock"],
        request_nonce: int,
        message_version: Optional[int] = None,
    ):
        if message_version is None:
            super().__init__()
        else:
            super().__init__(message_version)
        self._blocks = blocks
        self._request_nonce = request_nonce

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_blocks_response.CopyFrom(
            protobuf.GetBlocksResponse(
                raw_blocks=[block.to_proto_message() for block in self._blocks],
                request_nonce=self._request_nonce,
            )
        )
        logger.info(
            f"Sending a GetBlocksResponse with {builder.ByteSize() / 1000.0} kB"
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetBlocksResponse, message_version: int
    ) -> "GetBlocksResponse":
        blocks_list = [RawBlock.from_proto(pb) for pb in proto.raw_blocks]
        logger.info(
            f"\n\n<< Received a GetBlocksResponse with {len(blocks_list)} blocks and {proto.ByteSize() / 1000.0} kB size\n"
        )
        return GetBlocksResponse(
            blocks=blocks_list if proto.raw_blocks else [],
            request_nonce=proto.request_nonce,
            message_version=message_version,
        )

    def __str__(self):
        return (
            f"GetBlocksResponse{{\n"
            f"     blocks={self._blocks},\n"
            f"     request_nonce={self._request_nonce}\n"
            f"}} {super().__str__()}"
        )

    def associated_request(self):
        return GetBlocksRequest
