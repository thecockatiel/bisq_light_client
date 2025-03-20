from typing import TYPE_CHECKING, Optional, Union

from bisq.common.setup.log_setup import get_logger
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bitcoinj.script.script import Script
from bitcoinj.script.script_builder import ScriptBuilder
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.script.script_type import ScriptType
from electrum_min.transaction import (
    TxOutput as ElectrumTxOutput,
    PartialTxInput as ElectrumPartialTxInput,
)
from utils.preconditions import check_state

if TYPE_CHECKING:
    from bitcoinj.wallet.wallet import Wallet
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_input import TransactionInput


logger = get_logger(__name__)


# TODO
class TransactionOutput:

    def __init__(
        self,
        ec_tx_output: "ElectrumTxOutput",
        parent_tx: Optional["Transaction"] = None,
        available_for_spending: bool = True,
    ):
        self.parent = parent_tx
        self._ec_tx_output = ec_tx_output
        self.spent_by: Optional["TransactionInput"] = None
        self.available_for_spending = available_for_spending

    @staticmethod
    def from_coin_and_script(
        coin: Coin, script: Union[bytes, Script], parent_tx: "Transaction"
    ) -> "TransactionOutput":
        if isinstance(script, Script):
            script = script.program
        return TransactionOutput(
            ElectrumTxOutput(scriptpubkey=script, value=coin.value),
            parent_tx,
        )

    @staticmethod
    def from_coin_and_address(
        coin: Coin, address: Union[Address, str], parent_tx: "Transaction"
    ) -> "TransactionOutput":
        if isinstance(address, str):
            address = Address.from_string(address)
        return TransactionOutput(
            ElectrumTxOutput(
                scriptpubkey=ScriptBuilder.create_output_script(address).program,
                value=coin.value,
            ),
            parent_tx,
        )

    @staticmethod
    def from_utxo(
        partial_input: "ElectrumPartialTxInput", wallet: "Wallet"
    ) -> "TransactionOutput":
        parent_tx = wallet.get_transaction(partial_input.prevout.txid.hex())
        check_state(parent_tx is not None, "Parent transaction not found in wallet")
        output = parent_tx.outputs[partial_input.prevout.out_idx]
        return output

    @property
    def index(self):
        for i, output in enumerate(self.parent.outputs):
            if output == self:
                return i
        raise IllegalStateException("Output linked to wrong parent transaction?")

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

    @value.setter
    def value(self, value: int) -> None:
        self._ec_tx_output.value = value

    def get_script_pub_key(self) -> Script:
        return Script(self._ec_tx_output.scriptpubkey)

    @property
    def script_pub_key(self) -> bytes:
        return self._ec_tx_output.scriptpubkey

    def get_parent_transaction_hash(self) -> Optional[str]:
        return self.parent.get_tx_id()

    def get_parent_transaction_depth_in_blocks(self) -> int:
        if self.parent.confirmations:
            return self.parent.confidence.depth
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
                return wallet.is_mine(
                    self._ec_tx_output.address
                )  # TODO isn't this enough for all types ?
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

    @staticmethod
    def is_dust(output: Union["TransactionOutput", "ElectrumTxOutput"]) -> bool:
        # Transactions that are OP_RETURN can't be dust regardless of their value.
        if not isinstance(output, ElectrumTxOutput):
            output = output._ec_tx_output

        assert isinstance(output.value, int)  # we don't expend spend max like here

        if ScriptPattern.is_op_return(Script(output.scriptpubkey)):
            return False
        return output.value < TransactionOutput._get_min_non_dust_value(
            len(output.serialize_to_network())
        )

    def get_min_non_dust_value(self):
        return TransactionOutput._get_min_non_dust_value(
            len(self._ec_tx_output.serialize_to_network())
        )

    @staticmethod
    def _get_min_non_dust_value(serialized_size: int):
        # A typical output is 33 bytes (pubkey hash + opcodes) and requires an input of 148 bytes to spend so we add
        # that together to find out the total amount of data used to transfer this amount of value. Note that this
        # formula is wrong for anything that's not a P2PKH output, unfortunately, we must follow Bitcoin Core's
        # wrongness in order to ensure we're considered standard. A better formula would either estimate the
        # size of data needed to satisfy all different script types, or just hard code 33 below.
        fee_per_kb = 3000  # REFERENCE_DEFAULT_MIN_TX_FEE * 3
        size = serialized_size + 148
        return fee_per_kb * size // 1000

    def __str__(self):
        try:
            script = self.get_script_pub_key()
            buf = ["TxOut of "]
            buf.append(Coin.value_of(self.value).to_friendly_string())
            if (
                ScriptPattern.is_p2pkh(script)
                or ScriptPattern.is_p2wpkh(script)
                or ScriptPattern.is_p2sh(script)
            ):
                buf.append(" to ")
                buf.append(script.get_to_address(self.parent.params))
            elif ScriptPattern.is_p2pk(script):
                buf.append(" to pubkey ")
                buf.append(ScriptPattern.extract_key_from_p2pk(script).hex())
            elif ScriptPattern.is_sent_to_multi_sig(script):
                buf.append(" to multisig")
            else:
                buf.append(" (unknown type)")
            buf.append(" script:")
            buf.append(str(script))
            return "".join(buf)
        except Exception as e:
            raise RuntimeError(e) from e

    def __eq__(self, value):
        if isinstance(value, ElectrumTxOutput):
            return self._ec_tx_output == value
        if isinstance(value, TransactionOutput):
            return self._ec_tx_output == value._ec_tx_output
        return False
