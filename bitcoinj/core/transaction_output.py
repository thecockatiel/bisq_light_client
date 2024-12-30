from typing import TYPE_CHECKING, Optional

from bitcoinj.base.coin import Coin
from bitcoinj.core.sha_256_hash import Sha256Hash

if TYPE_CHECKING:
    from bitcoinj.script.script import Script
    from bitcoinj.core.transaction_input import TransactionInput


# TODO
class TransactionOutput:

    def __init__(self):
        self.spent_by: "TransactionInput" = None
        self.parent = None

    @property
    def index(self) -> int:
        raise NotImplementedError("index not implemented in TransactionOutput")

    def get_value(self) -> Coin:
        raise NotImplementedError("get_value not implemented in TransactionOutput")

    def get_script_pub_key(self) -> Script:
        raise NotImplementedError(
            "get_script_pub_key not implemented in TransactionOutput"
        )

    def get_parent_transaction_hash(self) -> Optional["Sha256Hash"]:
        """Returns the transaction hash that owns this output."""
        raise NotImplementedError(
            "get_parent_transaction_hash not implemented in TransactionOutput"
        )
