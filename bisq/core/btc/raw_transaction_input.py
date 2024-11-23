from dataclasses import dataclass, field
from bisq.common.util.utilities import bytes_as_hex_string
from bitcoinj.script.script import ScriptType
import proto.pb_pb2 as protobuf
from google.protobuf.message import Message
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload

# TODO: incomplete
@dataclass(kw_only=True)
class RawTransactionInput(NetworkPayload, PersistablePayload):
    index: int # Index of spending txo
    parent_transaction: bytes # Spending tx (fromTx)
    value: int = field(default=0)
    
    # Added at Bsq swap release
    # id of the org.bitcoinj.script.Script.ScriptType. Useful to know if input is segwit.
    # Lowest Script.ScriptType.id value is 1, so we use 0 as value for not defined
    script_type_id: int
    
    def to_proto_message(self) -> Message:
        return protobuf.RawTransactionInput(
            index=self.index,
            parent_transaction=self.parent_transaction,
            value=self.value,
            script_type_id=self.script_type_id,
        )
    
    @staticmethod
    def from_proto(self, proto: protobuf.RawTransactionInput):
        return RawTransactionInput(
            index=proto.index,
            parent_transaction=proto.parent_transaction,
            value=proto.value,
            script_type_id=proto.script_type_id,
        )
        
    @property
    def is_segwit(self):
        return self.is_p2wkh or self.is_p2wsh
    
    @property
    def is_p2wkh(self):
        return self.script_type_id == ScriptType.P2WPKH.id
    
    @property
    def is_p2wsh(self):
        return self.script_type_id == ScriptType.P2WSH.id

    def get_parent_tx_id(wallet_service):
        raise NotImplementedError()
    
    def validate(wallet_service):
        raise NotImplementedError()
    
    def __str__(self) -> str:
        return (f"RawTransactionInput("
                f"index={self.index}, "
                f"parent_transaction as HEX={bytes_as_hex_string(self.parent_transaction)}, "
                f"value={self.value}, "
                f"script_type_id={self.script_type_id})")

