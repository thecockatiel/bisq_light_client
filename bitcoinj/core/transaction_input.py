from typing import TYPE_CHECKING, Optional
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.script.script import Script
from electrum_min.bitcoin import witness_push
from electrum_min.transaction import TxOutpoint, PartialTxInput as ElectrumPartialTxInput

if TYPE_CHECKING:
    from electrum_min.transaction import TxInput as ElectrumTxInput
    from bitcoinj.core.transaction import Transaction


# TODO
class TransactionInput:
    NO_SEQUENCE = 0xFFFFFFFF
    SEQUENCE_LOCKTIME_DISABLE_FLAG = 1 << 31
    SEQUENCE_LOCKTIME_TYPE_FLAG = 1 << 22
    SEQUENCE_LOCKTIME_MASK = 0x0000FFFF
    UNCONNECTED = 0xFFFFFFFF

    def __init__(
        self,
        ec_tx_input: "ElectrumTxInput",
        parent_tx: Optional["Transaction"] = None,
        outpoint: Optional["TransactionOutPoint"] = None,
    ):
        self.parent = parent_tx
        self._ec_tx_input = ec_tx_input
        self.outpoint = outpoint
        self.value: Optional[Coin] = None

    @staticmethod
    def from_electrum_input(ec_tx_input: "ElectrumTxInput", parent_tx: Optional["Transaction"]):
        return TransactionInput(
            ec_tx_input,
            parent_tx,
            TransactionOutPoint(
                ec_tx_input.prevout.out_idx, ec_tx_input.prevout.txid.hex()
            ),
        )
    
    @staticmethod
    def from_output(tx_output: "TransactionOutput", parent_tx: Optional["Transaction"] = None):
        input = ElectrumPartialTxInput(
            prevout=TxOutpoint(tx_output.parent.get_tx_id(), tx_output.index),
            nsequence=TransactionInput.NO_SEQUENCE,
        )
        return TransactionInput(
            input,
            parent_tx,
            TransactionOutPoint.from_tx_output(tx_output),
        )

    @property
    def index(self):
        assert self.parent, "This input is not connected to a transaction."
        # find index or raise IllegalStateException
        try:
            return self.parent._electrum_transaction._inputs.index(self._ec_tx_input)
        except ValueError:
            raise IllegalStateException("Input linked to wrong parent transaction?")

    @property
    def connected_transaction(self) -> Optional["Transaction"]:
        return self.outpoint.from_tx if self.outpoint else None

    @property
    def connected_output(self) -> Optional["TransactionOutput"]:
        return self.outpoint.connected_output if self.outpoint else None

    @property
    def nsequence(self) -> int:
        return self._ec_tx_input.nsequence

    @property
    def has_sequence(self) -> bool:
        return self.nsequence != TransactionInput.NO_SEQUENCE

    @property
    def witness(self) -> Optional[str]:
        return self._ec_tx_input.witness.hex() if self.has_witness else None

    @witness.setter
    def witness(self, value: str) -> None:
        # TODO: used by trade_wallet_service.seller_adds_buyer_witness_to_deposit_tx. needs to be investigated
        raise NotImplementedError("TransactionInput.witness.setter Not implemented yet")

    @property
    def witness_elements(self):
        return self._ec_tx_input.witness_elements()

    @property
    def has_witness(self) -> bool:
        return bool(self.witness_elements)

    @property
    def has_relative_lock_time(self) -> bool:
        return self.nsequence & TransactionInput.SEQUENCE_LOCKTIME_DISABLE_FLAG == 0

    @property
    def is_opt_in_full_rbf(self) -> bool:
        return self.nsequence < TransactionInput.NO_SEQUENCE - 1

    @property
    def is_coin_base(self) -> bool:
        return self._ec_tx_input.is_coinbase_input()

    @property
    def script_sig(self) -> Optional[bytes]:
        return self._ec_tx_input.script_sig

    @property
    def script_pub_key(self) -> Optional[bytes]:
        return self._ec_tx_input.scriptpubkey

    def get_script_sig(self) -> Optional[Script]:
        """
        Returns the script that is fed to the referenced output (scriptPubKey) script in order to satisfy it: usually
        contains signatures and maybe keys, but can contain arbitrary data if the output script accepts it.
        """
        # Transactions that generate new coins don't actually have a script. Instead this
        # parameter is overloaded to be something totally different.
        script = None
        if self.script_sig:
            script = Script(self.script_sig)
        elif not script:
            script = Script(self.script_pub_key)
        return script

    def verify(self, output: "TransactionOutput") -> None:
        """
        Verifies that this input can spend the given output. Note that this input must be a part of a transaction.
        Also note that the consistency of the outpoint will be checked, even if this input has not been connected.
        :param output: The output that this input is supposed to spend.
        :raises ScriptException: If the script doesn't verify.
        :raises VerificationException: If the outpoint doesn't match the given output.
        """
        if output.parent:
            if self.outpoint.hash != output.parent.get_tx_id():
                raise VerificationException(
                    "This input does not refer to the tx containing the output."
                )
            if self.outpoint.index != output.index:
                raise VerificationException(
                    "This input refers to a different output on the given tx."
                )

        pub_key = output.get_script_pub_key()
        self.get_script_sig().correctly_spends(
            self.parent,
            self.index,
            self.witness_elements,
            output.get_value(),
            pub_key,
            Script.ALL_VERIFY_FLAGS,
        )
