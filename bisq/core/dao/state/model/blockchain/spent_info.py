from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class SpentInfo(PersistablePayload, ImmutableDaoStateModel):

    def __init__(
        self,
        block_height: int,
        tx_id: str,
        input_index: int,
    ):
        self._block_height = block_height
        self._tx_id = tx_id  # Spending tx
        self._input_index = input_index

    @property
    def block_height(self) -> int:
        return self._block_height

    @property
    def tx_id(self) -> str:
        return self._tx_id

    @property
    def input_index(self) -> int:
        return self._input_index

    @staticmethod
    def from_proto(proto: protobuf.SpentInfo) -> "SpentInfo":
        return SpentInfo(
            block_height=proto.block_height,
            tx_id=proto.tx_id,
            input_index=proto.input_index,
        )

    def to_proto_message(self) -> protobuf.SpentInfo:
        return protobuf.SpentInfo(
            block_height=self._block_height,
            tx_id=self._tx_id,
            input_index=self._input_index,
        )

    def __str__(self):
        return (
            f"SpentInfo{{\n"
            f"     blockHeight={self._block_height},\n"
            f"     txId='{self._tx_id}',\n"
            f"     inputIndex={self._input_index}\n"
            f"}}"
        )
