from typing import Union
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx_type import (
    AccountingTxType,
)
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.util.string_utils import hex_decode_last_4_bytes
import pb_pb2 as protobuf
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx_output import (
    AccountingTxOutput,
)


class AccountingTx(NetworkPayload):

    def __init__(
        self,
        type: AccountingTxType,
        outputs: list["AccountingTxOutput"],
        tx_id_or_truncated_bytes: Union[str, bytes],
    ):
        self.type = type
        self.outputs = outputs

        if isinstance(tx_id_or_truncated_bytes, str):
            # We store only last 4 bytes to have a unique ID. Chance for collusion is very low, and we take that risk that
            # one object might get overridden in a hashset by the colluding truncatedTxId and all other data being the same as well.
            self.truncated_tx_id = hex_decode_last_4_bytes(tx_id_or_truncated_bytes)
        elif isinstance(tx_id_or_truncated_bytes, bytes):
            self.truncated_tx_id = tx_id_or_truncated_bytes
        else:
            raise IllegalArgumentException(
                "tx_id_or_truncated_bytes must be either str or bytes"
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return protobuf.AccountingTx(
            type=self.type.value,
            outputs=[output.to_proto_message() for output in self.outputs],
            truncated_tx_id=self.truncated_tx_id,
        )

    @staticmethod
    def from_proto(proto: "protobuf.AccountingTx"):
        return AccountingTx(
            AccountingTxType(proto.type),
            [AccountingTxOutput.from_proto(output) for output in proto.outputs],
            proto.truncated_tx_id,
        )

    def __str__(self):
        return (
            f"AccountingTx{{\n"
            f"               type='{self.type}',\n"
            f"               outputs={self.outputs},\n"
            f"               truncatedTxId={self.truncated_tx_id.hex()}\n"
            f"          }}"
        )
