from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput


# TODO
class TransactionOutPoint:
    MESSAGE_LENGTH = 36

    def __init__(self):
        self.index = 0
        self.from_tx: "Transaction" = None
        self.connected_output: "TransactionOutput" = None
        self.hash: bytes = None
