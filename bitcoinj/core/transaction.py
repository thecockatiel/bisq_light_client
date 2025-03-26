from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.util.utilities import bytes_as_hex_string
from bitcoinj.base.coin import Coin
from bitcoinj.core.block import Block
from bitcoinj.core.sha_256_hash import Sha256Hash
from bitcoinj.core.transaction_confidence import TransactionConfidence
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.core.varint import get_var_int_bytes
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.crypto.transaction_signature import TransactionSignature
from bitcoinj.script.script_builder import ScriptBuilder
from electrum_min.bitcoin import opcodes
from electrum_min.transaction import (
    PartialTransaction as PartialElectrumTransaction,
    Transaction as ElectrumTransaction,
    TxInput as ElectrumTxInput,
    TxOutput as ElectrumTxOutput,
    PartialTxOutput as ElectrumPartialTxOutput,
    PartialTxInput as ElectrumPartialTxInput,
)
from utils.wrappers import LazySequenceWrapper
from bitcoinj.script.script import Script
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.core.transaction_input import TransactionInput

if TYPE_CHECKING:
    from bitcoinj.core.address import Address
    from bitcoinj.wallet.wallet import Wallet
    from electrum_min.util import TxMinedInfo
    from bitcoinj.core.network_parameters import NetworkParameters


def date_time_format(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# TODO
class Transaction:
    LOCKTIME_THRESHOLD = 500000000

    def __init__(
        self,
        params: "NetworkParameters",
        payload_bytes_or_tx: Optional[Union[bytes, ElectrumTransaction, str]] = None,
        *,
        psbt=False,
    ) -> None:
        if isinstance(payload_bytes_or_tx, str):
            payload_bytes_or_tx = bytes.fromhex(payload_bytes_or_tx)

        if isinstance(payload_bytes_or_tx, ElectrumTransaction):
            self._electrum_transaction = payload_bytes_or_tx
        elif isinstance(payload_bytes_or_tx, bytes):

            if psbt:
                self._electrum_transaction = PartialElectrumTransaction.from_raw_psbt(
                    payload_bytes_or_tx
                )
            else:
                self._electrum_transaction = ElectrumTransaction(payload_bytes_or_tx)
                self._electrum_transaction.deserialize()
                tx = self._electrum_transaction
                # init partial tx from tx but keep witnesses
                res = PartialElectrumTransaction()
                for txin in tx.inputs():
                    ptx = ElectrumPartialTxInput.from_txin(txin, strip_witness=False)
                    res._inputs.append(
                        ptx
                    )
                res._outputs = [
                    ElectrumPartialTxOutput.from_txout(txout) for txout in tx.outputs()
                ]
                res.version = tx.version
                res.locktime = tx.locktime
                res._cached_network_ser = tx._cached_network_ser
                self._electrum_transaction = res
        else:
            self._electrum_transaction = PartialElectrumTransaction()

        self.params = params

        self._update_time: Optional[datetime] = None
        """
        This is either the time the transaction was broadcast as measured from the local clock, or the time from the
        block in which it was included. Note that this can be changed by re-orgs so the wallet may update this field.
        Old serialized transactions don't have this field, thus null is valid. It is used for returning an ordered
        list of transactions from a wallet, which is helpful for presenting to users.
        """

        self._included_in_best_chain_at: Optional[datetime] = None
        """Date of the block that includes this transaction on the best chain"""

        self.memo: Optional[str] = None
        """
        it should be retrieved from the wallet
        it's called "label" in electrum
        """
        self.confidence: Optional["TransactionConfidence"] = None

    @property
    def update_time(self):
        """
        Returns the earliest time at which the transaction was seen (broadcast or included into the chain),
        or the epoch if that information isn't available.
        """
        if self._update_time is None:
            # Older wallets did not store this field. Set to the epoch.
            self._update_time = datetime.fromtimestamp(0, tz=timezone.utc)
        return self._update_time

    @update_time.setter
    def update_time(self, value: Optional[datetime]):
        self._update_time = value

    @property
    def confirmations(self):
        return self.confidence.confirmations if self.confidence else None

    @property
    def is_pending(self):
        return (
            self.confidence.confidence_type == TransactionConfidenceType.PENDING
            if self.confidence
            else False
        )

    @property
    def lock_time(self):
        return self._electrum_transaction.locktime

    @lock_time.setter
    def lock_time(self, value: int):
        self._electrum_transaction.locktime = value

    @cached_property
    def inputs(self):
        from bitcoinj.core.transaction_input import TransactionInput

        return LazySequenceWrapper(
            self._electrum_transaction.inputs,
            lambda tx_input, idx: TransactionInput.from_electrum_input(
                self.params, tx_input, self
            ),
        )

    @cached_property
    def outputs(self):
        from bitcoinj.core.transaction_output import TransactionOutput

        return LazySequenceWrapper(
            self._electrum_transaction.outputs,
            lambda tx_output, idx: TransactionOutput(tx_output, self),
        )

    @property
    def version(self):
        return self._electrum_transaction.version

    @version.setter
    def version(self, value: int):
        self._electrum_transaction.version = value

    def get_tx_id(self) -> str:
        return self._electrum_transaction.txid()

    def get_wtx_id(self) -> "Sha256Hash":
        return self._electrum_transaction.wtxid()

    def bitcoin_serialize(self, include_sigs=True) -> bytes:
        """include_sigs signals whether to include scriptSigs and witnesses"""
        return bytes.fromhex(
            self._electrum_transaction.serialize_to_network(include_sigs=include_sigs)
        )

    @property
    def included_in_best_chain_at(self):
        return self._included_in_best_chain_at

    @included_in_best_chain_at.setter
    def included_in_best_chain_at(self, value: Optional[datetime]):
        self._included_in_best_chain_at = value

    def get_sig_op_count(self):
        sig_ops = 0
        for tx_input in self.inputs:
            sig_ops += Script.get_program_sig_op_count(tx_input.script_sig)
        for tx_output in self.outputs:
            sig_ops += Script.get_program_sig_op_count(tx_output.script_pub_key)
        return sig_ops

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

    def get_input_sum(self) -> Coin:
        input_total = Coin.ZERO()

        for tx_input in self.inputs:
            if tx_input.value:
                input_total = input_total.add(tx_input.get_value())

        return input_total

    def get_output_sum(self) -> Coin:
        total_out = Coin.ZERO()

        for output in self.outputs:
            if output.value is not None:
                total_out = total_out.add(output.get_value())

        return total_out

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

    @property
    def appears_in_hashes(self) -> Optional[dict[str, int]]:
        # todo
        return None

    def get_fee(self) -> Optional[Coin]:
        fee = self._electrum_transaction.get_fee()
        if fee is None:
            return None
        return Coin.value_of(fee)

    def is_any_output_spent(self) -> bool:
        for output in self.outputs:
            if not output.available_for_spending:
                return True
        return False

    @staticmethod
    def verify(network: "NetworkParameters", tx: "Transaction") -> None:
        # since we use electrum under the hood, the first check is to run deserialize on it.
        try:
            tx._electrum_transaction.invalidate_ser_cache()
            tx._electrum_transaction.deserialize()
            message_size = tx.get_message_size()
        except Exception as e:
            if "negative int to unsigned" in str(e):
                raise VerificationException.NegativeValueOutput() from e
            raise VerificationException(e) from e

        if not tx.inputs or not tx.outputs:
            raise VerificationException.EmptyInputsOrOutputs()

        if message_size > Block.MAX_BLOCK_SIZE:
            raise VerificationException.LargerThanMaxBlockSize()

        outpoints = set()
        for tx_in in tx.inputs:
            if tx_in.outpoint in outpoints:
                raise VerificationException.DuplicatedOutPoint()
            outpoints.add(tx_in.outpoint)

        value_out = Coin.ZERO()
        for tx_out in tx.outputs:
            value = tx_out.get_value()
            if value.signum() < 0:
                raise VerificationException.NegativeValueOutput()
            try:
                value_out = value_out.add(value)
            except:
                raise VerificationException.ExcessiveValue()

            if network.has_max_money() and value_out > network.get_max_money():
                raise VerificationException.ExcessiveValue()

        if tx.is_coin_base:
            if len(tx.inputs[0].script_sig) < 2 or len(tx.inputs[0].script_sig) > 100:
                raise VerificationException.CoinbaseScriptSizeOutOfRange()
        else:
            for tx_in in tx.inputs:
                if tx_in.is_coin_base:
                    raise VerificationException.UnexpectedCoinbaseInput()

    def maybe_finalize(self, wallet: "Wallet"):
        if (
            isinstance(self._electrum_transaction, PartialElectrumTransaction)
            and not self._electrum_transaction.is_complete()
        ):
            wallet.add_info_from_wallet(self._electrum_transaction)
            self._electrum_transaction.finalize_psbt()

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
            ).hash_bytes

        if not anyone_can_pay and sign_all:
            hash_sequence = Sha256Hash.twice_of(
                b"".join(input.nsequence.to_bytes(4, "little") for input in self.inputs)
            ).hash_bytes

        if sign_all:
            hash_outputs = Sha256Hash.twice_of(
                b"".join(
                    output.value.to_bytes(8, "little")
                    + get_var_int_bytes(len(output.script_pub_key))
                    + output.script_pub_key
                    for output in self.outputs
                )
            ).hash_bytes
        elif basic_sig_hash_type == TransactionSigHash.SINGLE.int_value and index < len(
            self.outputs
        ):
            output = self.outputs[index]
            hash_outputs = Sha256Hash.twice_of(
                output.value.to_bytes(8, "little")
                + get_var_int_bytes(len(output.script_pub_key))
                + output.script_pub_key
            ).hash_bytes

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

    def hash_for_signature(
        self,
        input_index: int,
        connected_script: Union[bytes, "Script"],
        sig_hash_type: Union[TransactionSigHash, int],
        anyone_can_pay: Optional[bool] = None,
    ):
        if isinstance(connected_script, Script):
            connected_script = connected_script.program

        if isinstance(sig_hash_type, TransactionSigHash):
            sig_hash_type = TransactionSignature.calc_sig_hash_value(
                sig_hash_type, anyone_can_pay
            )

        tx = None
        try:
            tx = Transaction(self.params, self.bitcoin_serialize(include_sigs=False))
            tx = tx._electrum_transaction
        except:
            # Should not happen unless we were given a totally broken transaction.
            raise

        for i, tx_in in enumerate(tx.inputs()):
            tx_in.script_sig = b""
            setattr(tx_in, "_TxInput__scriptpubkey", None)
            tx_in.witness = b""

        connected_script = Script.remove_all_instances_of_op(
            connected_script, opcodes.OP_CODESEPARATOR
        )

        input = tx._inputs[input_index]
        input.script_sig = connected_script
        setattr(input, "_TxInput__scriptpubkey", connected_script)

        # using variable or getters for inputs and outputs in different places is intentional.

        if (sig_hash_type & 0x1F) == TransactionSigHash.NONE.int_value:
            # SIGHASH_NONE means no outputs are signed at all - the signature is effectively for a "blank cheque".
            tx._outputs = []
            for i in range(len(tx._inputs)):
                if i != input_index:
                    tx._inputs[i].nsequence = 0
        elif (sig_hash_type & 0x1F) == TransactionSigHash.SINGLE.int_value:
            # SIGHASH_SINGLE means only sign the output at the same index as the input (ie, my output).
            if input_index >= len(tx.outputs()):
                # The input index is beyond the number of outputs, it's a buggy signature made by a broken wallet.
                return Sha256Hash.wrap(
                    "0100000000000000000000000000000000000000000000000000000000000000"
                ).hash_bytes

            tx._outputs = tx._outputs[: input_index + 1]
            for i in range(input_index):
                tx._outputs[i] = ElectrumTxOutput(scriptpubkey=b"", value=-1)
            # The signature isn't broken by new versions of the transaction issued by other parties.
            for i in range(len(tx._inputs)):
                if i != input_index:
                    tx._inputs[i].nsequence = 0

        if (
            sig_hash_type & TransactionSigHash.ANYONECANPAY.int_value
        ) == TransactionSigHash.ANYONECANPAY.int_value:
            tx._inputs = []
            tx._inputs.append(input)

        tx.invalidate_ser_cache()
        bos = bytes.fromhex(tx.serialize_to_network(include_sigs=True))
        bos = bos + (0x000000FF & sig_hash_type).to_bytes(4, "little")
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
        size = self.get_message_size()
        vsize = self.get_vsize()

        s.append(f"{indent}weight: {weight} wu, ")
        if size != vsize:
            s.append(f"{vsize} virtual bytes, ")
        s.append(f"{size} bytes\n")

        if self.update_time:
            s.append(f"{indent}updated: {date_time_format(self.update_time)}\n")
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
                script = bytes_as_hex_string(self.inputs[0].script_sig)
                script2 = bytes_as_hex_string(self.outputs[0].script_pub_key)
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
                    s.append(f"{tx_in.get_script_sig()}")
                    value = tx_in.get_value()
                    if value is not None:
                        s.append(f"  {value.to_friendly_string()} ({value})")
                    s.append("\n")
                    if tx_in.has_witness:
                        s.append(
                            f"{indent}        witness:{bytes_as_hex_string(tx_in.witness)}\n"
                        )

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
                    s.append(f"{script_pub_key}")
                    s.append(f" ({script_pub_key.program.hex()})")
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

    def add_input(self, tx_io: Union["TransactionInput", "TransactionOutput"]):
        if isinstance(tx_io, TransactionOutput):
            tx_io = TransactionInput.from_output(tx_io)
        if not isinstance(tx_io._ec_tx_input, ElectrumPartialTxInput):
            tx_io._ec_tx_input = ElectrumPartialTxInput.from_txin(tx_io._ec_tx_input)
        # we manually manage inputs and outputs because electrums sorts them by default (BIP69)
        if self._electrum_transaction._inputs is None:
            self._electrum_transaction._inputs = []
        self._electrum_transaction._inputs.append(tx_io._ec_tx_input)
        self._electrum_transaction.invalidate_ser_cache()
        return tx_io

    def add_output(self, tx_output: "TransactionOutput"):
        electrum_output = tx_output._ec_tx_output
        if not isinstance(electrum_output, ElectrumPartialTxOutput):
            electrum_output = ElectrumPartialTxOutput.from_txout(electrum_output)
        if self._electrum_transaction._outputs is None:
            self._electrum_transaction._outputs = []
        self._electrum_transaction._outputs.append(electrum_output)
        self._electrum_transaction.invalidate_ser_cache()
        return tx_output

    def add_output_using_coin_and_address(self, coin: Coin, address: "Address"):
        from bitcoinj.core.transaction_output import TransactionOutput

        output = TransactionOutput(
            self,
            ElectrumTxOutput(
                scriptpubkey=ScriptBuilder.create_output_script(address).program,
                value=coin.value,
            ),
        )
        self.add_output(output)

    def clear_inputs(self):
        self._electrum_transaction._inputs = None
        self._electrum_transaction._cached_network_ser = None
        self.inputs.invalidate()

    def clear_outputs(self):
        self._electrum_transaction._outputs = None
        self._electrum_transaction._cached_network_ser = None
        self.outputs.invalidate()
