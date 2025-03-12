from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.blockchain.base_block import BaseBlock
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf
from bisq.core.dao.state.model.blockchain.tx import Tx


class Block(BaseBlock, PersistablePayload, ImmutableDaoStateModel):
    """
    The Block which gets persisted in the DaoState. During parsing transactions can be
    added to the txs list, therefore it is not an immutable list.

    It is difficult to make the block immutable by using the same pattern we use with Tx or TxOutput because we add the
    block at the beginning of the parsing to the daoState and add transactions during parsing. We need to have the state
    updated during parsing. If we would set then after the parsing the immutable block we might have inconsistent data.
    There might be a way to do it but it comes with high complexity and risks so for now we prefer to have that known
    issue with not being fully immutable at that level.

    An empty block (no BSQ txs) has 146 bytes in Protobuffer serialized form.
    """

    def __init__(
        self,
        height: int,
        time: int,
        hash: str,
        previous_block_hash: Optional[str],
        txs: list["Tx"] = None,
    ):
        super().__init__(height, time, hash, previous_block_hash)
        # We cannot make it immutable as we add transactions during parsing.
        self._txs = txs or []

    def to_proto_message(self) -> protobuf.BaseBlock:
        builder = self.get_base_block_builder()
        builder.block.CopyFrom(
            protobuf.Block(
                txs=[tx.to_proto_message() for tx in self._txs],
            )
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BaseBlock) -> "Block":
        block_proto = proto.block
        txs = [Tx.from_proto(tx_proto) for tx_proto in block_proto.txs]
        return Block(
            height=proto.height,
            time=proto.time,
            hash=proto.hash,
            previous_block_hash=proto.previous_block_hash,
            txs=txs,
        )

    def add_tx(self, tx: "Tx"):
        self._txs.append(tx)

    # We cannot provide the same modification guarantees as java, but we can at least make it clear that
    # the list content should not be modified.
    # NOTE: this can be expensive, needs to be checked later
    def get_txs(self):
        return tuple(self._txs)

    def __str__(self):
        return (
            f"Block{{\n"
            f"    txs={self._txs}\n"  #
            f"}} {super().__str__()}"
        )
