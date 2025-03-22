from typing import TYPE_CHECKING, Optional
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.script.script import Script
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
        if outpoint:
            self.outpoint = outpoint
        elif ec_tx_input.prevout:
            self.outpoint = TransactionOutPoint(
                ec_tx_input.prevout.out_idx,
                ec_tx_input.prevout.txid.hex(),
            )

    @property
    def value(self):
        return self._ec_tx_input.value_sats() or 0
    
    def get_value(self): 
        return Coin.value_of(self.value)

    @staticmethod
    def from_electrum_input(params: "NetworkParameters", ec_tx_input: "ElectrumTxInput", parent_tx: Optional["Transaction"]):
        from bitcoinj.core.transaction import Transaction

        if ec_tx_input.utxo:
            tx = Transaction(params, ec_tx_input.utxo.serialize_as_bytes())
            outpoint = TransactionOutPoint.from_tx(
                tx,
                ec_tx_input.prevout.out_idx, 
            )
        elif ec_tx_input.prevout:
            outpoint = TransactionOutPoint(
                ec_tx_input.prevout.out_idx,
                ec_tx_input.prevout.txid.hex(),
            )
        
        return TransactionInput(
            ec_tx_input,
            parent_tx,
            outpoint,
        )
    
    @staticmethod
    def from_output(tx_output: "TransactionOutput", parent_tx: Optional["Transaction"] = None):
        input = ElectrumPartialTxInput(
            prevout=TxOutpoint(bytes.fromhex(tx_output.parent.get_tx_id()), tx_output.index),
            nsequence=TransactionInput.NO_SEQUENCE,
        )
        if parent_tx:
            input.utxo = parent_tx._electrum_transaction
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
        return self.outpoint.connected_tx if self.outpoint else None

    @property
    def connected_output(self) -> Optional["TransactionOutput"]:
        return self.outpoint.connected_output if self.outpoint else None

    @property
    def nsequence(self) -> int:
        return self._ec_tx_input.nsequence
    
    @nsequence.setter
    def nsequence(self, value: int) -> None:
        self._ec_tx_input.nsequence = value

    @property
    def has_sequence(self) -> bool:
        return self.nsequence != TransactionInput.NO_SEQUENCE

    @property
    def witness(self) -> Optional[bytes]:
        return self._ec_tx_input.witness

    @witness.setter
    def witness(self, value: Optional[bytes]) -> None:
        self._ec_tx_input.witness = value

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
    
    @script_sig.setter
    def script_sig(self, value: bytes) -> None:
        self._ec_tx_input.script_sig = value

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

    def __str__(self):
        s = ["TxIn"]
        try:
            if self.is_coin_base:
                s.append(": COINBASE")
            else:
                s.append(f" for [{self.outpoint}]: {self.get_script_sig()}")
                flags = ", ".join(
                    filter(
                    None,
                    [
                        "witness" if self.has_witness else None,
                        f"sequence: {hex(self.nsequence)}" if self.has_sequence else None,
                        "opts into full RBF" if self.is_opt_in_full_rbf else None,
                    ],
                    )
                )
                if flags:
                    s.append(f" ({flags})")
                return "".join(s)
        except Exception as e:
            raise RuntimeError(e)

    def __eq__(self, value):
        if isinstance(value, ElectrumTxInput):
            return self._ec_tx_input == value
        if isinstance(value, TransactionInput):
            return self._ec_tx_input == value._ec_tx_input
        return False
