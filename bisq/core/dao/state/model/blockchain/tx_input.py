from typing import Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class TxInput(PersistablePayload, ImmutableDaoStateModel):
    """
    An input is really just a reference to the spending output. It gets identified by the
    txId and the index of that output. We use TxOutputKey to encapsulate that.
    """

    def __init__(
        self,
        connected_tx_output_tx_id: str,
        connected_tx_output_index: int,
        pub_key: Optional[str] = None,
    ):
        self.connected_tx_output_tx_id = connected_tx_output_tx_id
        self.connected_tx_output_index = connected_tx_output_index
        self.pub_key = pub_key
        """as hex string. Optional."""

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        builder = protobuf.TxInput(
            connected_tx_output_tx_id=self.connected_tx_output_tx_id,
            connected_tx_output_index=self.connected_tx_output_index,
        )
        if self.pub_key:
            builder.pub_key = self.pub_key
        return builder

    @staticmethod
    def from_proto(proto: protobuf.TxInput):
        return TxInput(
            connected_tx_output_tx_id=proto.connected_tx_output_tx_id,
            connected_tx_output_index=proto.connected_tx_output_index,
            pub_key=proto.pub_key if proto.pub_key else None,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_connected_tx_output_key(self):
        return TxOutputKey(
            self.connected_tx_output_tx_id, self.connected_tx_output_index
        )

    def __str__(self):
        return (
            "TxInput{\n"
            f"                    connectedTxOutputTxId='{self.connected_tx_output_tx_id}',\n"
            f"                    connectedTxOutputIndex={self.connected_tx_output_index},\n"
            f"                    pubKey={self.pub_key}\n"
            "               }"
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, TxInput):
            return False
        return (
            self.connected_tx_output_tx_id == other.connected_tx_output_tx_id
            and self.connected_tx_output_index == other.connected_tx_output_index
            and self.pub_key == other.pub_key
        )

    def __hash__(self):
        return hash(
            (
                self.connected_tx_output_tx_id,
                self.connected_tx_output_index,
                self.pub_key,
            )
        )
