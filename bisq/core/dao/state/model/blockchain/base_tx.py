from abc import ABC
from bisq.core.dao.state.model.blockchain.tx_input import TxInput
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class BaseTx(ImmutableDaoStateModel, ABC):
    """
    The base class for the Tx classes with all common immutable data fields.

    TxOutputs are not added here as the sub classes use different data types.
    As not all subclasses implement PersistablePayload we leave it to the sub classes to implement the interface.
    A getBaseTxBuilder method though is available.
    """

    def __init__(
        self,
        tx_version: str,
        id: str,
        block_height: int,
        block_hash: str,
        time: int,
        tx_inputs: tuple[TxInput],
    ):
        self.tx_version = tx_version
        self.id = id
        self.block_height = block_height
        self.block_hash = block_hash
        self.time = time
        self.tx_inputs = tx_inputs

    def get_base_tx_builder(self):
        return protobuf.BaseTx(
            tx_version=self.tx_version,
            id=self.id,
            block_height=self.block_height,
            block_hash=self.block_hash,
            time=self.time,
            tx_inputs=[tx_input.to_proto_message() for tx_input in self.tx_inputs],
        )

    def __str__(self) -> str:
        return (
            f"BaseTx{{\n"
            f"     tx_version='{self.tx_version}',\n"
            f"     id='{self.id}',\n"
            f"     block_height={self.block_height},\n"
            f"     block_hash='{self.block_hash}',\n"
            f"     time={self.time},\n"
            f"     tx_inputs={self.tx_inputs}\n"
            f"}}"
        )
