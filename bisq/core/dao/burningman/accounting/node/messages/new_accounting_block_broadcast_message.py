from typing import Optional
from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
    AccountingBlock,
)
from bisq.core.network.p2p.storage.messages.broadcast_message import BroadcastMessage
import pb_pb2 as protobuf


# copied from NewBlockBroadcastMessage
class NewAccountingBlockBroadcastMessage(BroadcastMessage):
    def __init__(
        self,
        block: "AccountingBlock",
        pub_key: str,
        signature: bytes,
        message_version: Optional[int] = None,
    ):
        if message_version is None:
            super().__init__()
        else:
            super().__init__(message_version)
        self.block = block
        self.pub_key = pub_key
        self.signature = signature

    def to_proto_message(self):
        return protobuf.NewAccountingBlockBroadcastMessage(
            block=self.block.to_proto_message(),
            pub_key=self.pub_key,
            signature=self.signature,
        )

    def to_proto_network_envelope(self):
        builder = self.get_network_envelope_builder()
        builder.new_accounting_block_broadcast_message.CopyFrom(self.to_proto_message())
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.NewAccountingBlockBroadcastMessage,
        message_version: int,
    ):
        return NewAccountingBlockBroadcastMessage(
            block=AccountingBlock.from_proto(proto.block),
            pub_key=proto.pub_key,
            signature=proto.signature,
            message_version=message_version,
        )

    def __eq__(self, value):
        return (
            isinstance(value, NewAccountingBlockBroadcastMessage)
            and self.block == value.block
            and self.pub_key == value.pub_key
            and self.signature == value.signature
            and self.message_version == value.message_version
        )

    def __hash__(self):
        return hash((self.block, self.pub_key, self.signature, self.message_version))
