from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_logger
from bitcoinj.base.coin import Coin
from bitcoinj.core.sha_256_hash import Sha256Hash
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.script.script import Script
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.script.script_type import ScriptType

if TYPE_CHECKING:
    from bitcoinj.wallet.wallet import Wallet
    from electrum_min.transaction import TxOutput as ElectrumTxOutput
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_input import TransactionInput


logger = get_logger(__name__)


# TODO
class TransactionOutput:

    def __init__(
        self,
        tx: "Transaction",
        ec_tx_output: "ElectrumTxOutput",
        index: int,
        available_for_spending: bool = True,
    ):
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
                return confidence.depth
        return -1

    def is_for_wallet(self, wallet: "Wallet") -> bool:
        """Returns true if this output is to a key, or an address we have the keys for, in the wallet."""
        try:
            script = self.get_script_pub_key()
            if ScriptPattern.is_p2pk(script):
                return (
                    wallet.find_key_from_pub_key(
                        ScriptPattern.extract_key_from_p2pk(script), ScriptType.P2PK
                    )
                    is not None
                )
            elif ScriptPattern.is_p2sh(script):
                raise NotImplementedError("P2SH support is not implemented yet")
            elif ScriptPattern.is_p2pkh(script):
                return (
                    wallet.find_key_from_pub_key_hash(
                        ScriptPattern.extract_hash_from_p2pkh(script), ScriptType.P2PKH
                    )
                    is not None
                )
            elif ScriptPattern.is_p2wpkh(script):
                return (
                    wallet.find_key_from_pub_key_hash(
                        ScriptPattern.extract_hash_from_p2wpkh(script),
                        ScriptType.P2WPKH,
                    )
                    is not None
                )
            else:
                return False
        except Exception as e:
            # Just means we didn't understand the output of this transaction: ignore it.
            logger.debug(
                "Could not parse tx {} output script: {}".format(
                    (
                        self.parent.get_tx_id()
                        if self.parent is not None
                        else "(no parent)"
                    ),
                    str(e),
                )
            )
            return False
