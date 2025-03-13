from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from bisq.common.util.utilities import bytes_as_hex_string
from bitcoinj.script.script_type import ScriptType
import pb_pb2 as protobuf
from google.protobuf.message import Message
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from utils.data import raise_required
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.btc.wallet.wallet_service import WalletService
    from bitcoinj.core.transaction_input import TransactionInput


@dataclass
class RawTransactionInput(NetworkPayload, PersistablePayload):
    index: int = field(default_factory=raise_required)  # Index of spending txo
    parent_transaction: bytes = field(
        default_factory=raise_required
    )  # Spending tx (fromTx)
    value: int = field(default=0)

    # Added at Bsq swap release
    # id of the org.bitcoinj.script.Script.ScriptType. Useful to know if input is segwit.
    # Lowest Script.ScriptType.id value is 1, so we use 0 as value for not defined
    script_type_id: int = field(default=0)

    @staticmethod
    def from_transaction_input(input: "TransactionInput"):
        try:
            script_type_id = (
                input.connected_output.get_script_pub_key().get_script_type().id
            )
        except:
            script_type_id = 0

        return RawTransactionInput(
            index=input.outpoint.index,
            parent_transaction=input.connected_output.parent.bitcoin_serialize(),
            value=input.value,
            script_type_id=script_type_id,
        )

    def to_proto_message(self) -> Message:
        return protobuf.RawTransactionInput(
            index=self.index,
            parent_transaction=self.parent_transaction,
            value=self.value,
            script_type_id=self.script_type_id,
        )

    @staticmethod
    def from_proto(proto: protobuf.RawTransactionInput):
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

    def get_parent_tx_id(self, wallet_service: "WalletService"):
        raise wallet_service.get_tx_from_serialized_tx(
            self.parent_transaction
        ).get_tx_id()

    def validate(self, wallet_service: "WalletService"):
        assert (
            self.parent_transaction is not None
        ), "parent_transaction must not be None"
        tx = wallet_service.get_tx_from_serialized_tx(self.parent_transaction)
        if self.index < 0 or self.index >= len(tx.outputs):
            raise ValueError("Input index out of range.")
        output_value = tx.outputs[self.index].value
        check_argument(
            self.value == output_value,
            f"Input value ({self.value}) mismatches connected tx output value ({output_value}).",
        )
        script_pub_key = tx.outputs[self.index].get_script_pub_key()
        script_type = script_pub_key.get_script_type() if script_pub_key else None
        check_argument(
            self.script_type_id <= 0
            or (script_type and script_type.id == self.script_type_id),
            f"Input script_type_id ({self.script_type_id}) mismatches connected tx output script_type_id "
            f"({script_type.name if script_type is not None else None}.id = {script_type.id if script_type else 0}).",
        )

    def __str__(self) -> str:
        return (
            f"RawTransactionInput("
            f"index={self.index}, "
            f"parent_transaction as HEX={bytes_as_hex_string(self.parent_transaction)}, "
            f"value={self.value}, "
            f"script_type_id={self.script_type_id})"
        )
