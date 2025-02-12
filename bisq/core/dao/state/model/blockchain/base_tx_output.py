from abc import ABC

from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.state.model.blockchain.pub_key_script import PubKeyScript
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from typing import Optional
import pb_pb2 as protobuf


class BaseTxOutput(ImmutableDaoStateModel, ABC):
    """Base class for TxOutput classes containing the immutable bitcoin specific blockchain data."""

    def __init__(
        self,
        index: int,
        value: int,
        tx_id: str,
        pub_key_script: Optional[PubKeyScript],
        address: Optional[str],
        op_return_data: Optional[bytes],
        block_height: int,
    ):
        self.index = index
        self.value = value
        self.tx_id = tx_id

        # Before v0.9.6 it was only set if dumpBlockchainData was set to true but we changed that with 0.9.6
        # so that it is always set. We still need to support it because of backward compatibility.
        self.pub_key_script = pub_key_script  # Has about 50 bytes, total size of TxOutput is about 300 bytes.
        self.address = address
        self.op_return_data = op_return_data  # JsonExclude
        self.block_height = block_height

    def get_json_dict(self):
        return {
            "index": self.index,
            "value": self.value,
            "txId": self.tx_id,
            "pubKeyScript": self.pub_key_script,
            "address": self.address,
            "blockHeight": self.block_height,
        }

    def get_raw_tx_output_builder(self):
        builder = protobuf.BaseTxOutput(
            index=self.index,
            value=self.value,
            tx_id=self.tx_id,
            block_height=self.block_height,
            pub_key_script=(
                self.pub_key_script.to_proto_message()
                if self.pub_key_script is not None
                else None
            ),
            address=self.address,
            op_return_data=self.op_return_data,
        )
        return builder

    def get_key(self):
        return TxOutputKey(self.tx_id, self.index)

    def __str__(self):
        return (
            f"BaseTxOutput{{\n"
            f"     index={self.index},\n"
            f"     value={self.value},\n"
            f"     txId='{self.tx_id}',\n"
            f"     pubKeyScript={self.pub_key_script},\n"
            f"     address='{self.address}',\n"
            f"     opReturnData={bytes_as_hex_string(self.op_return_data)},\n"
            f"     blockHeight={self.block_height}\n"
            f"}}"
        )
