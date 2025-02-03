from typing import TYPE_CHECKING, Optional

from bitcoinj.base.coin import Coin
from bitcoinj.core.sha_256_hash import Sha256Hash
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.script.script import Script

if TYPE_CHECKING:
    from electrum_min.transaction import TxOutput as ElectrumTxOutput
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_input import TransactionInput


# TODO
class TransactionOutput:

    def __init__(self, tx: "Transaction", ec_tx_output: "ElectrumTxOutput", index: int, available_for_spending: bool = True):
        self.parent = tx
        self._ec_tx_output = ec_tx_output
        self.index = index
        self.spent_by: Optional["TransactionInput"] = None
        self.available_for_spending = available_for_spending

    def get_value(self) -> Coin:
        assert isinstance(
            self._ec_tx_output.value, int
        )  # we don't expend spend max like here
        return Coin.value_of(self._ec_tx_output.value)

    @property
    def value(self) -> int:
        assert isinstance(
            self._ec_tx_output.value, int
        )  # we don't expend spend max like here
        return self._ec_tx_output.value

    def get_script_pub_key(self) -> Script:
        return Script(self._ec_tx_output.scriptpubkey)

    @property
    def script_pub_key(self) -> bytes:
        return self._ec_tx_output.scriptpubkey

    def get_parent_transaction_hash(self) -> Optional[str]:
        return self.parent.get_tx_id()
    
    def get_parent_transaction_depth_in_blocks(self) -> int:
        if self.parent is not None:
            confidence = self.parent.get_confidence()
            if confidence.confidence_type == TransactionConfidenceType.BUILDING:
                return confidence.get_depth_in_blocks()
        return -1

    def is_mine(self, transaction_bad) -> bool:
        """Returns true if this output is to a key, or an address we have the keys for, in the wallet."""
        # TODO: raise NotImplementedError("TransactionOutput.is_mine not implemented yet")
        return False
