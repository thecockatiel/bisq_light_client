from typing import TYPE_CHECKING

from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bitcoinj.script.script import Script
    from bitcoinj.core.transaction_input import TransactionInput


# TODO
class TransactionOutput:

    def __init__(self):
        self.spent_by: "TransactionInput" = None

    @property
    def index(self) -> int:
        raise NotImplementedError("index not implemented in TransactionOutput")

    def get_value(self) -> Coin:
        raise NotImplementedError("get_value not implemented in TransactionOutput")

    def get_script_pub_key(self) -> Script:
        raise NotImplementedError(
            "get_script_pub_key not implemented in TransactionOutput"
        )
