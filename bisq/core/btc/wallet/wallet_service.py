
from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.crypto.hash import get_sha256_hash

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction_confidence import TransactionConfidence

# TODO
class WalletService(ABC):
    
    def __init__(self, params: "NetworkParameters"):
        super().__init__()
        self.params = params
    
    def get_transaction(hash_or_tx_id: Union[bytes, Optional[str]]) -> Optional["Transaction"]:
        if hash_or_tx_id is None:
            return None
        if isinstance(hash_or_tx_id, str):
            hash_or_tx_id = get_sha256_hash(hash_or_tx_id)
        raise RuntimeError("WalletService.get_transaction Not implemented yet")
    
    def get_tx_from_serialized_tx(self, tx: bytes) -> Optional["Transaction"]:
        return Transaction(self.params, tx)
    
    def get_confidence_for_tx_id(self, tx_id: Optional[str])-> Optional['TransactionConfidence']:     
        raise RuntimeError("WalletService.get_confidence_for_tx_id Not implemented yet")
