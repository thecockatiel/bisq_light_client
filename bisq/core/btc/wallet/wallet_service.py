
from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.crypto.hash import get_sha256_hash

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction

# TODO
class WalletService(ABC):
    
    def get_transaction(hash_or_tx_id: Union[bytes, Optional[str]]) -> Optional["Transaction"]:
        if hash_or_tx_id is None:
            return None
        if isinstance(hash_or_tx_id, str):
            hash_or_tx_id = get_sha256_hash(hash_or_tx_id)
        raise RuntimeError("WalletService.get_transaction Not implemented yet")