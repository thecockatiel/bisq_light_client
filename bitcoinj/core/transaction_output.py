from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bitcoinj.core.transaction_input import TransactionInput


# TODO
class TransactionOutput:

    def __init__(self):
        self.spent_by: "TransactionInput" = None

    @property
    def index(self) -> int:
        raise NotImplementedError("index not implemented in TransactionOutput")