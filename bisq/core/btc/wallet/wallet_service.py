
from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.setup.log_setup import get_logger
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction_confidence import TransactionConfidence

logger = get_logger(__name__)

# TODO
class WalletService(ABC):
    
    def __init__(self, wallets_setup: "WalletsSetup", preferences: "Preferences", fee_service: "FeeService"):
        super().__init__()
        self.wallets_setup = wallets_setup
        self.preferences = preferences
        self.fee_service = fee_service
        
        self.params = self.wallets_setup.params
    
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

    def get_tx_fee_for_withdrawal_per_vbyte(self) -> Coin:
        fee = Coin.value_of(self.preferences.get_withdrawal_tx_fee_in_vbytes()) if self.preferences.get_use_custom_withdrawal_tx_fee() else \
                self.fee_service.get_tx_fee_per_vbyte()
        logger.info(f"tx fee = {fee.to_friendly_string()}")
        return fee
    
    def get_last_block_seen_height(self) -> int:
        raise RuntimeError("WalletService.get_last_block_seen_height Not implemented yet")
    