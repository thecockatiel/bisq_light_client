from typing import TYPE_CHECKING
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.dao.state.model.blockchain.base_block import BaseBlock
from bisq.core.dao.node.full.raw_tx import RawTx
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block


class RawBlock(BaseBlock, NetworkPayload):
    """
    A block derived from the BTC blockchain and filtered for BSQ relevant transactions, though the transactions are not
    verified at that stage. That block is passed to lite nodes over the P2P network. The validation is done by the lite
    nodes themselves but the transactions are already filtered for BSQ only transactions to keep bandwidth requirements
    low.
    Sent over wire.
    """

    def __init__(
        self,
        height: int,
        time: int,
        hash: str,
        previous_block_hash: str,
        raw_txs: tuple["RawTx"],
    ):
        super().__init__(height, time, hash, previous_block_hash)
        self._raw_txs = raw_txs

    @staticmethod
    def from_block(block: "Block") -> "RawBlock":
        txs = tuple(RawTx.from_tx(tx) for tx in block.get_txs())
        return RawBlock(
            block.height,
            block.time,
            block.hash,
            block.previous_block_hash,
            txs,
        )

    def to_proto_message(self):
        builder = self.get_base_block_builder()
        builder.raw_block.CopyFrom(
            protobuf.RawBlock(
                raw_txs=[tx.to_proto_message() for tx in self._raw_txs],
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BaseBlock) -> "RawBlock":
        raw_block_proto = proto.raw_block
        raw_txs = (
            tuple(RawTx.from_proto(tx) for tx in raw_block_proto.raw_txs)
            if raw_block_proto.raw_txs
            else tuple["RawTx"]()
        )
        return RawBlock(
            proto.height,
            proto.time,
            proto.hash,
            proto.previous_block_hash,
            raw_txs,
        )

    def __str__(self) -> str:
        return (
            f"RawBlock{{\n"
            f"     height={self.height},\n"
            f"     time={self.time},\n"
            f"     hash='{self.hash}',\n"
            f"     previous_block_hash='{self.previous_block_hash}',\n"
            f"     raw_txs={self._raw_txs}\n"
            f"}}"
        )
