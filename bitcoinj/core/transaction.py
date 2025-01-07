from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Union

from bitcoinj.base.coin import Coin
from bitcoinj.core.sha_256_hash import Sha256Hash
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.core.varint import get_var_int_bytes
from bitcoinj.crypto.transaction_signature import TransactionSignature
from electrum_min.bitcoin import opcodes
from electrum_min.transaction import Transaction as ElectrumTransaction, TxOutput
from utils.wrappers import LazySequenceWrapper
from bitcoinj.script.script import Script

if TYPE_CHECKING:
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.network_parameters import NetworkParameters


def date_time_format(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# TODO
class Transaction:
    LOCKTIME_THRESHOLD = 500000000

    def __init__(
        self, params: "NetworkParameters", payload_bytes: bytes = None
    ) -> None:
        self._electrum_transaction = ElectrumTransaction(payload_bytes)
        self.params = params

        self.updated_at: Optional[datetime] = None
        """
        This is either the time the transaction was broadcast as measured from the local clock, or the time from the
        block in which it was included. Note that this can be changed by re-orgs so the wallet may update this field.
        Old serialized transactions don't have this field, thus null is valid. It is used for returning an ordered
        list of transactions from a wallet, which is helpful for presenting to users.
        """

        self.included_in_best_chain_at: Optional[datetime] = None
        """Date of the block that includes this transaction on the best chain"""

    @property
    def lock_time(self):
        return self._electrum_transaction.locktime

    @cached_property
    def inputs(self):
        from bitcoinj.core.transaction_input import TransactionInput

        return LazySequenceWrapper(
            self._electrum_transaction.inputs,
            lambda tx_input, idx: TransactionInput(self, tx_input, idx),
        )

    @cached_property
    def outputs(self):
        from bitcoinj.core.transaction_output import TransactionOutput

        return LazySequenceWrapper(
            self._electrum_transaction.outputs,
            lambda tx_output, idx: TransactionOutput(self, tx_output, idx),
        )

    @property
    def version(self):
        return self._electrum_transaction.version

    def get_tx_id(self) -> str:
        return self._electrum_transaction.txid()

    def get_wtx_id(self) -> "Sha256Hash":
        return self._electrum_transaction.wtxid()

    def bitcoin_serialize(self) -> bytes:
        return bytes.fromhex(self._electrum_transaction.serialize_to_network())

    def get_update_time(self):
        """
        Returns the earliest time at which the transaction was seen (broadcast or included into the chain),
        or the epoch if that information isn't available.
        """
        if self.updated_at is None:
            # Older wallets did not store this field. Set to the epoch.
            self.updated_at = datetime.fromtimestamp(0, tz=timezone.utc)
        return self.updated_at

    def get_included_in_best_chain_at(self):
        return self.included_in_best_chain_at

    def get_confidence(self, *, context=None, table=None) -> "TransactionConfidence":
        raise RuntimeError("Transaction.get_confidence Not implemented yet")

    def serialize(self) -> bytes:
        return self._electrum_transaction.serialize_as_bytes()

    @property
    def has_witnesses(self) -> bool:
        return any(input.has_witness for input in self.inputs)

    def get_message_size(self) -> int:
        return self._electrum_transaction.estimated_total_size()

    def get_weight(self) -> int:
        return self._electrum_transaction.estimated_weight()

    def get_vsize(self) -> int:
        return self._electrum_transaction.estimated_size()

    @property
    def is_time_locked(self):
        return self.lock_time > 0

    @property
    def has_relative_lock_time(self):
        if self._electrum_transaction.version < 2:
            return False
        return any(input.has_relative_lock_time for input in self.inputs)

    @property
    def is_opt_in_full_rbf(self):
        return any(input.is_opt_in_full_rbf for input in self.inputs)

    @property
    def is_coin_base(self):
        return len(self.inputs) == 1 and self.inputs[0].is_coin_base

    def get_fee(self) -> Optional[Coin]:
        if self._electrum_transaction.get_fee() is None:
            return None
        return Coin.value_of(self._electrum_transaction.get_fee())

    def hash_for_witness_signature(
        self,
        index: int,
        script_code: Union[bytes, "Script"],
        prev_value: "Coin",
        sig_hash: "TransactionSigHash",
        anyone_can_pay: bool,
    ) -> bytes:
        if isinstance(script_code, Script):
            script_code = script_code.program
        sig_hash_type = TransactionSignature.calc_sig_hash_value(
            sig_hash, anyone_can_pay
        )
        hash_prevouts = bytes(32)
        hash_sequence = bytes(32)
        hash_outputs = bytes(32)
        basic_sig_hash_type = sig_hash_type & 0x1F
        anyone_can_pay = (
            sig_hash_type & TransactionSigHash.ANYONECANPAY.int_value
        ) == TransactionSigHash.ANYONECANPAY.int_value
        sign_all = (basic_sig_hash_type != TransactionSigHash.SINGLE.int_value) and (
            basic_sig_hash_type != TransactionSigHash.NONE.int_value
        )

        if not anyone_can_pay:
            hash_prevouts = Sha256Hash.twice_of(
                b"".join(
                    bytes(reversed(bytes.fromhex(input.outpoint.hash)))
                    + input.outpoint.index.to_bytes(4, "little")
                    for input in self.inputs
                )
            )

        if not anyone_can_pay and sign_all:
            hash_sequence = Sha256Hash.twice_of(
                b"".join(
                    input.nsequence.to_bytes(4, "little") for input in self.inputs
                )
            )

        if sign_all:
            hash_outputs = Sha256Hash.twice_of(
                b"".join(
                    output.value.to_bytes(8, "little")
                    + get_var_int_bytes(len(output.script_pub_key))
                    + output.script_pub_key
                    for output in self.outputs
                )
            )
        elif basic_sig_hash_type == TransactionSigHash.SINGLE.int_value and index < len(
            self.outputs
        ):
            output = self.outputs[index]
            hash_outputs = Sha256Hash.twice_of(
                output.value.to_bytes(8, "little")
                + get_var_int_bytes(len(output.script_pub_key))
                + output.script_pub_key
            )

        bos = bytearray()
        bos.extend(self.version.to_bytes(4, "little"))
        bos.extend(hash_prevouts)
        bos.extend(hash_sequence)
        input = self.inputs[index]
        bos.extend(bytes(reversed(bytes.fromhex(input.outpoint.hash))))
        bos.extend(input.outpoint.index.to_bytes(4, "little"))
        bos.extend(get_var_int_bytes(len(script_code)))
        bos.extend(script_code)
        bos.extend(prev_value.value.to_bytes(8, "little"))
        bos.extend(input.nsequence.to_bytes(4, "little"))
        bos.extend(hash_outputs)
        bos.extend(self.lock_time.to_bytes(4, "little"))
        bos.extend((sig_hash_type & 0x000000FF).to_bytes(4, "little"))

        return Sha256Hash.twice_of(bos).hash_bytes
    
    def hash_for_signature(self, input_index: int, connected_script: Union[bytes, "Script"], sig_hash_type: Union[TransactionSigHash, int], anyone_can_pay: Optional[bool] = None):
        if isinstance(connected_script, Script):
            connected_script = connected_script.program
        
        if isinstance(sig_hash_type, TransactionSigHash):
            sig_hash_type = TransactionSignature.calc_sig_hash_value(sig_hash_type, anyone_can_pay)
        
        tx = None
        try:
            tx = Transaction(self.params, self.bitcoin_serialize())
            tx._electrum_transaction.deserialize()
            tx = tx._electrum_transaction
        except:
            # Should not happen unless we were given a totally broken transaction.
            raise
        
        for i, tx_in in enumerate(tx.inputs()):
            setattr(tx_in, "_TxInput__scriptpubkey", None)
            tx_in.witness = None
            
        connected_script = Script.remove_all_instances_of_op(connected_script, opcodes.OP_CODESEPARATOR)
        
        input = tx._inputs[input_index]
        input.script_sig = connected_script
        setattr(input, "_TxInput__scriptpubkey", connected_script)
        
        # using variable or getters for inputs and outputs in different places is intentional.
        
        if (sig_hash_type & 0x1f) == TransactionSigHash.NONE.int_value:
            # SIGHASH_NONE means no outputs are signed at all - the signature is effectively for a "blank cheque".
            tx._outputs = []
            for i in range(len(tx._inputs)):
                if i != input_index:
                    tx._inputs[i].nsequence = 0
        elif (sig_hash_type & 0x1f) == TransactionSigHash.SINGLE.int_value:
            # SIGHASH_SINGLE means only sign the output at the same index as the input (ie, my output).
            if input_index >= len(tx.outputs()):
                # The input index is beyond the number of outputs, it's a buggy signature made by a broken wallet.
                return Sha256Hash.wrap("0100000000000000000000000000000000000000000000000000000000000000").hash_bytes
            
            tx._outputs = tx._outputs[:input_index + 1]
            for i in range(input_index):
                tx._outputs[i] = TxOutput(scriptpubkey=b"", value=-1)
            # The signature isn't broken by new versions of the transaction issued by other parties.
            for i in range(len(tx._inputs)):
                if i != input_index:
                    tx._inputs[i].nsequence = 0
        
        if (sig_hash_type & TransactionSigHash.ANYONECANPAY.int_value) == TransactionSigHash.ANYONECANPAY.int_value:
            tx._inputs = []
            tx._inputs.append(input)
        
        tx.invalidate_ser_cache()
        bos = bytes.fromhex(tx.serialize_to_network(include_sigs=True, force_legacy=False))
        bos = bos + (0x000000ff & sig_hash_type).to_bytes(4, "little")
        return Sha256Hash.twice_of(bos).hash_bytes

    def to_debug_str(self, chain=None, indent=None):
        if indent is None:
            indent = ""

        s = []
        tx_id, wtx_id = self.get_tx_id(), self.get_wtx_id()
        s.append(f"{indent}{tx_id}")
        if wtx_id != tx_id:
            s.append(f", wtxid {wtx_id}")
        s.append("\n")

        weight = self.get_weight()
        size = len(self.bitcoin_serialize())
        vsize = self.get_vsize()

        s.append(f"{indent}weight: {weight} wu, ")
        if size != vsize:
            s.append(f"{vsize} virtual bytes, ")
        s.append(f"{size} bytes\n")

        if self.updated_at:
            s.append(f"{indent}updated: {date_time_format(self.updated_at)}\n")
        if self.included_in_best_chain_at:
            s.append(
                f"{indent}included in best chain at: {date_time_format(self.included_in_best_chain_at)}\n"
            )
        if self.version != 1:
            s.append(f"{indent}version {self.version}\n")

        if self.is_time_locked:
            s.append(f"{indent}time locked until ")
            if self.lock_time < Transaction.LOCKTIME_THRESHOLD:
                s.append(f"block {self.lock_time}")
                # Chain estimation not implemented
            else:
                s.append(
                    date_time_format(
                        datetime.fromtimestamp(self.lock_time, tz=timezone.utc)
                    )
                )
            s.append("\n")

        if self.has_relative_lock_time:
            s.append(f"{indent}has relative lock time\n")
        if self.is_opt_in_full_rbf:
            s.append(f"{indent}opts into full replace-by-fee\n")

        if self.is_coin_base:
            try:
                script = self.inputs[0].script_sig.hex()
                script2 = self.outputs[0].script_pub_key.hex()
            except Exception:
                script = "???"
                script2 = "???"
            s.append(
                f"{indent}   == COINBASE TXN (scriptSig {script})  (scriptPubKey {script2})\n"
            )
            return "".join(s)

        if self.inputs:
            for i, tx_in in enumerate(self.inputs):
                s.append(f"{indent}   in   ")
                try:
                    s.append(f"{tx_in.script_sig.hex()}")
                    value = tx_in.value
                    if value is not None:
                        s.append(f"  {value.to_friendly_string()} ({value})")
                    s.append("\n")
                    if tx_in.has_witness:
                        s.append(f"{indent}        witness:{tx_in.witness}\n")

                    outpoint = tx_in.outpoint
                    connected_output = outpoint.connected_output
                    s.append(f"{indent}        ")
                    if connected_output is not None:
                        script_pub_key = connected_output.get_script_pub_key()
                        script_type = script_pub_key.get_script_type()
                        if script_type is not None:
                            s.append(
                                f"{script_type.name} addr:{script_pub_key.get_to_address(self.params)} "
                            )
                        else:
                            s.append("unknown script type")
                    else:
                        s.append("unconnected")

                    s.append(f"  outpoint: {outpoint}\n")
                    if tx_in.has_sequence:
                        s.append(f"{indent}        sequence:{hex(tx_in.nsequence)}\n")
                        if tx_in.is_opt_in_full_rbf:
                            s.append(", opts into full RBF")
                        if self.version >= 2 and tx_in.has_relative_lock_time:
                            s.append(", has RLT")
                        s.append("\n")
                except Exception as e:
                    s.append(f"[exception: {e}]\n")
        else:
            s.append(f"{indent}   INCOMPLETE: No inputs!\n")

        for tx_out in self.outputs:
            s.append(f"{indent}   out  ")
            try:
                script_pub_key = tx_out.get_script_pub_key()
                if script_pub_key.program:
                    s.append(f"({script_pub_key.hex()})")
                else:
                    s.append("<no scriptPubKey>")
                s.append(
                    f"  {tx_out.get_value().to_friendly_string()} ({tx_out.get_value()})\n"
                )
                s.append(f"{indent}        ")
                script_type = script_pub_key.get_script_type()
                if script_type is not None:
                    s.append(
                        f"{script_type.name} addr:{script_pub_key.get_to_address(self.params)} "
                    )
                else:
                    s.append("unknown script type")
                # is available for spending not implemented
                s.append("\n")
            except Exception as e:
                s.append(f"[exception: {e}]\n")

        fee = self.get_fee()
        if fee is not None:
            s.append(f"{indent}   fee  ")
            s.append(fee.multiply(1000).divide(weight).to_friendly_string())
            s.append("/wu, ")
            if size != vsize:
                s.append(fee.multiply(1000).divide(vsize).to_friendly_string())
                s.append("/vkB, ")
            s.append(fee.multiply(1000).divide(size).to_friendly_string())
            s.append("/kB  ")
            s.append(fee.to_friendly_string())
            s.append("\n")

        return "".join(s)

    def __str__(self):
        return self.to_debug_str(None, None)
