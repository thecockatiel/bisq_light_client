from typing import TYPE_CHECKING, Optional
from bisq.common.capabilities import Capabilities
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.initial_data_request import InitialDataRequest
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
from bisq.core.network.p2p.supported_capabilities_message import (
    SupportedCapabilitiesMessage,
)
from bisq.core.network.p2p.node_address import NodeAddress
import pb_pb2 as protobuf


# Taken from GetBlocksRequest
class GetAccountingBlocksRequest(
    NetworkEnvelope,
    DirectMessage,
    SendersNodeAddressMessage,
    SupportedCapabilitiesMessage,
    InitialDataRequest,
):

    def __init__(
        self,
        from_block_height: int,
        nonce: int,
        sender_node_address: "NodeAddress",
        supported_capabilities: Optional["Capabilities"] = None,
        message_version: Optional[int] = None,
    ):
        if message_version is None:
            super().__init__()
        else:
            super().__init__(message_version)

        if supported_capabilities is None:
            supported_capabilities = Capabilities.app

        self.from_block_height = from_block_height
        self.nonce = nonce
        # Added after version 1.0.1. Can be null if received from older clients.
        self.sender_node_address = sender_node_address
        # Added after version 1.0.1. Can be null if received from older clients.
        self.supported_capabilities = supported_capabilities

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.get_accounting_blocks_request.CopyFrom(
            protobuf.GetAccountingBlocksRequest(
                from_block_height=self.from_block_height,
                nonce=self.nonce,
                sender_node_address=(
                    self.sender_node_address.to_proto_message()
                    if self.sender_node_address
                    else None
                ),
                supported_capabilities=(
                    Capabilities.to_int_list(self.supported_capabilities)
                    if self.supported_capabilities
                    else None
                ),
            )
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.GetAccountingBlocksRequest, message_version: int
    ) -> "GetAccountingBlocksRequest":
        proto_node_address = proto.sender_node_address
        sender_node_address = (
            None
            if not proto_node_address.host_name
            else NodeAddress.from_proto(proto_node_address)
        )
        supported_capabilities = (
            None
            if not proto.supported_capabilities
            else Capabilities.from_int_list(proto.supported_capabilities)
        )
        return GetAccountingBlocksRequest(
            from_block_height=proto.from_block_height,
            nonce=proto.nonce,
            sender_node_address=sender_node_address,
            supported_capabilities=supported_capabilities,
            message_version=message_version,
        )

    def __str__(self):
        return (
            f"GetAccountingBlocksRequest{{\n"
            f"     fromBlockHeight={self.from_block_height},\n"
            f"     nonce={self.nonce},\n"
            f"     senderNodeAddress={self.sender_node_address},\n"
            f"     supportedCapabilities={self.supported_capabilities}\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other):
        return (
            isinstance(other, GetAccountingBlocksRequest)
            and self.from_block_height == other.from_block_height
            and self.nonce == other.nonce
            and self.sender_node_address == other.sender_node_address
            and self.supported_capabilities == other.supported_capabilities
        )

    def __hash__(self):
        return hash(
            (
                self.from_block_height,
                self.nonce,
                self.sender_node_address,
            )
        )
