
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from bitcoinj.core.transaction_input import TransactionInput
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.network_parameters import NetworkParameters

# TODO
class Transaction:
    
    def __init__(self, params: "NetworkParameters", payload_bytes: bytes = None, offset = 0) -> None:
        self.params = params
        self.offset = offset
        self.payload_bytes = payload_bytes
        self.lock_time = 0
        self.inputs: list["TransactionInput"] = []
        self.outputs: list["TransactionOutput"] = []
        
        self.updated_at: Optional[datetime] = None
        """
        This is either the time the transaction was broadcast as measured from the local clock, or the time from the
        block in which it was included. Note that this can be changed by re-orgs so the wallet may update this field.
        Old serialized transactions don't have this field, thus null is valid. It is used for returning an ordered
        list of transactions from a wallet, which is helpful for presenting to users.
        """
        
        self.included_in_best_chain_at: Optional[datetime] = None
        """Date of the block that includes this transaction on the best chain"""
        
        raise RuntimeError("Transaction Not implemented yet")
    
    def get_tx_id(self) -> bytes:
        raise RuntimeError("Transaction.get_tx_id Not implemented yet")
    
    def get_w_tx_id(self) -> bytes:
        raise RuntimeError("Transaction.get_w_tx_id Not implemented yet")
    
    def bitcoin_serialize(self) -> bytes:
        raise RuntimeError("Transaction.bitcoin_serialize Not implemented yet")
    
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
    
    def get_confidence(self, *, context = None, table = None) -> "TransactionConfidence":
        raise RuntimeError("Transaction.get_confidence Not implemented yet")