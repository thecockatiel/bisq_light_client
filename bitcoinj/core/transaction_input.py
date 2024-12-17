from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.core.transaction_out_point import TransactionOutPoint


# TODO
class TransactionInput:
    def __init__(self):
        self.outpoint: "TransactionOutPoint" = None
        """Data needed to connect to the output of the transaction we're gathering coins from."""
        self._sequence = int
        """Allows for altering transactions after they were broadcast. Values below NO_SEQUENCE-1 mean it can be altered."""

    @property
    def connected_transaction(self) -> Optional["Transaction"]:
        return self.outpoint.from_tx if self.outpoint else None

    @property
    def connected_output(self) -> Optional["TransactionOutput"]:
        return self.outpoint.connected_output if self.outpoint else None
    
    @property
    def sequence_number(self):
        return self._sequence
    
    @sequence_number.setter
    def sequence_number(self, value):
        self._sequence = value
