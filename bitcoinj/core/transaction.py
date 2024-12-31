from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Sequence

from bitcoinj.core.sha_256_hash import Sha256Hash
from electrum_min.transaction import Transaction as ElectrumTransaction
from utils.wrappers import LazySequenceWrapper

if TYPE_CHECKING:
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.core.transaction_input import TransactionInput
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.network_parameters import NetworkParameters


# TODO
class Transaction:

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
        return LazySequenceWrapper(self._electrum_transaction.inputs, lambda tx_input, idx: TransactionInput(self, tx_input, idx))
    
    @cached_property
    def outputs(self):
        from bitcoinj.core.transaction_output import TransactionOutput
        return LazySequenceWrapper(self._electrum_transaction.outputs, lambda tx_output, idx: TransactionOutput(self, tx_output, idx))

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
    
    def has_witnesses(self):
        return any(input.has_witness for input in self.inputs)
    
    def get_message_size(self):
        return self._electrum_transaction.estimated_total_size()

    def to_debug_str(self, chain = None, indent = None):
        raise RuntimeError("Transaction.to_debug_str Not implemented yet")
    
    def __str__(self):
        return self.to_debug_str(None, None)
