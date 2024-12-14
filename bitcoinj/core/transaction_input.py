from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.core.transaction_out_point import TransactionOutPoint


# TODO
class TransactionInput:
    def __init__(self):
        self.outpoint: "TransactionOutPoint" = None

    @property
    def connected_transaction(self) -> Optional["Transaction"]:
        return self.outpoint.from_tx if self.outpoint else None

    @property
    def connected_output(self) -> Optional["TransactionOutput"]:
        return self.outpoint.connected_output if self.outpoint else None
