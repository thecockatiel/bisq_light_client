from typing import Optional
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
from bisq.core.dao.node.full.raw_block import RawBlock
import pb_pb2 as protobuf

# We remove the CapabilityRequiringPayload interface to avoid risks that new BSQ blocks are not well distributed in
# case the capability is not exchanged at the time when the message is sent. We need to improve the capability handling
# so that we can be sure that we know the actual capability of the peer.


# This message is sent only to lite DAO nodes (full nodes get block from their local bitcoind)
class NewBlockBroadcastMessage(BroadcastMessage):
    def __init__(
        self,
        block: "RawBlock",
        message_version: Optional[int] = None,
    ):
        if message_version is None:
            super().__init__()
        else:
            super().__init__(message_version)
        self.block = block

    def to_proto_message(self):
        return protobuf.NewBlockBroadcastMessage(
            raw_block=self.block.to_proto_message()
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.new_block_broadcast_message.CopyFrom(self.block.to_proto_message())
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.NewBlockBroadcastMessage,
        message_version: int,
    ):
        return NewBlockBroadcastMessage(
            block=RawBlock.from_proto(proto.raw_block),
            message_version=message_version,
        )
