from typing import Iterable, Optional
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
    AccountingBlock,
)
from bisq.core.dao.burningman.accounting.node.messages.get_accounting_blocks_request import (
    GetAccountingBlocksRequest,
)
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.extended_data_size_permission import (
    ExtendedDataSizePermission,
)
from bisq.core.network.p2p.initial_data_response import InitialDataResponse
import pb_pb2 as protobuf


logger = get_logger(__name__)


# Taken from GetBlocksResponse
class GetAccountingBlocksResponse(
    NetworkEnvelope, DirectMessage, ExtendedDataSizePermission, InitialDataResponse
):

    def __init__(
        self,
        blocks: Iterable["AccountingBlock"],
        request_nonce: int,
        pub_key: str,
        signature: bytes,
        message_version: Optional[int] = None,
    ):
        if message_version is None:
            super().__init__()
        else:
            super().__init__(message_version)
        self.blocks = tuple(blocks) if not isinstance(blocks, tuple) else blocks
        self.request_nonce = request_nonce
        self.pub_key = pub_key
        self.signature = signature

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_accounting_blocks_response.CopyFrom(
            protobuf.GetAccountingBlocksResponse(
                blocks=[block.to_proto_message() for block in self.blocks],
                request_nonce=self.request_nonce,
                pub_key=self.pub_key,
                signature=self.signature,
            )
        )
        logger.info(
            f"Sending a GetAccountingBlocksResponse with {builder.ByteSize() / 1000.0} kB"
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetAccountingBlocksResponse, message_version: int
    ) -> "GetAccountingBlocksResponse":
        blocks_list = tuple(AccountingBlock.from_proto(pb) for pb in proto.blocks)
        logger.info(
            f"\n\n<< Received a GetAccountingBlocksResponse with {len(blocks_list)} blocks and {proto.ByteSize() / 1000.0} kB size\n"
        )
        return GetAccountingBlocksResponse(
            blocks=blocks_list if proto.blocks else [],
            request_nonce=proto.request_nonce,
            pub_key=proto.pub_key,
            signature=proto.signature,
            message_version=message_version,
        )

    def __str__(self):
        return (
            f"GetAccountingBlocksResponse{{\n"
            f"     blocks={self.blocks},\n"
            f"     request_nonce={self.request_nonce}\n"
            f"}} {super().__str__()}"
        )

    def associated_request(self):
        return GetAccountingBlocksRequest

    def __eq__(self, other):
        return (
            isinstance(other, GetAccountingBlocksResponse)
            and self.blocks == other.blocks
            and self.request_nonce == other.request_nonce
            and self.pub_key == other.pub_key
            and self.signature == other.signature
        )

    def __hash__(self):
        return hash((self.blocks, self.request_nonce, self.pub_key, self.signature))
