from abc import ABC
from typing import Optional
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class BaseBlock(ImmutableDaoStateModel, ABC):
    """
    The base class for RawBlock and Block containing the common immutable bitcoin
    blockchain specific data.
    """

    def __init__(
        self,
        height: int,
        time: int,
        hash: str,
        previous_block_hash: Optional[str] = None,
    ):
        self.height = height
        self.time = time  # in ms
        self.hash = hash
        self.previous_block_hash = (
            previous_block_hash  # is None in case of first block in the blockchain
        )

    def get_base_block_builder(self) -> protobuf.BaseBlock:
        base_block = protobuf.BaseBlock(
            height=self.height,
            time=self.time,
            hash=self.hash,
            previous_block_hash=self.previous_block_hash,
        )
        return base_block

    def __str__(self) -> str:
        return (
            f"BaseBlock{{\n"
            f"     height={self.height},\n"
            f"     time={self.time},\n"
            f"     hash='{self.hash}',\n"
            f"     previous_block_hash='{self.previous_block_hash}'\n"
            f"}}"
        )
