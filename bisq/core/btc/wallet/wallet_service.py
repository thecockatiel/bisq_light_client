from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.listeners.balance_listener import BalanceListener
from bitcoinj.base.coin import Coin
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bitcoinj.wallet.listeners.wallet_change_event_listener import (
        WalletChangeEventListener,
    )
    from bitcoinj.core.address import Address
    from bisq.core.btc.listeners.address_confidence_listener import (
        AddressConfidenceListener,
    )
    from bitcoinj.wallet.wallet import Wallet
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.transaction_output import TransactionOutput

logger = get_logger(__name__)


# TODO
class WalletService(ABC):

    def __init__(
        self,
        wallets_setup: "WalletsSetup",
        preferences: "Preferences",
        fee_service: "FeeService",
    ):
        super().__init__()
        self.wallets_setup = wallets_setup
        self.preferences = preferences
        self.fee_service = fee_service

        self.params = self.wallets_setup.params
        self.wallet: Optional["Wallet"] = None
        self.aes_key: Optional[bytes] = None
        self.balance_listeners = ThreadSafeSet["BalanceListener"]()

    def is_wallet_ready(self):
        return self.wallet is not None

    def is_encrypted(self) -> bool:
        return self.wallet.is_encrypted() if self.wallet else False

    def get_transaction(
        hash_or_tx_id: Union[bytes, Optional[str]]
    ) -> Optional["Transaction"]:
        if hash_or_tx_id is None:
            return None
        if isinstance(hash_or_tx_id, bytes):
            hash_or_tx_id = hash_or_tx_id.hex()
        raise RuntimeError("WalletService.get_transaction Not implemented yet")

    def get_tx_from_serialized_tx(self, tx: bytes) -> Optional["Transaction"]:
        return Transaction(self.params, tx)

    def get_confidence_for_tx_id(
        self, tx_id: Optional[str]
    ) -> Optional["TransactionConfidence"]:
        raise RuntimeError("WalletService.get_confidence_for_tx_id Not implemented yet")

    def get_tx_fee_for_withdrawal_per_vbyte(self) -> Coin:
        fee = (
            Coin.value_of(self.preferences.get_withdrawal_tx_fee_in_vbytes())
            if self.preferences.get_use_custom_withdrawal_tx_fee()
            else self.fee_service.get_tx_fee_per_vbyte()
        )
        logger.info(f"tx fee = {fee.to_friendly_string()}")
        return fee

    def get_last_block_seen_height(self) -> int:
        raise RuntimeError(
            "WalletService.get_last_block_seen_height Not implemented yet"
        )

    def get_all_recent_transactions(self, include_dead: bool) -> list["Transaction"]:
        raise RuntimeError(
            "WalletService.get_all_recent_transactions Not implemented yet"
        )

    def is_transaction_output_mine(
        self, transaction_output: "TransactionOutput"
    ) -> bool:
        raise RuntimeError(
            "WalletService.is_transaction_output_mine Not implemented yet"
        )

    def is_output_script_convertible_to_address(
        self, transaction_output: "TransactionOutput"
    ) -> bool:
        raise RuntimeError(
            "WalletService.is_output_script_convertible_to_address Not implemented yet"
        )

    def get_address_string_from_output(
        self, transaction_output: "TransactionOutput"
    ) -> Optional[str]:
        raise RuntimeError(
            "WalletService.get_address_string_from_output Not implemented yet"
        )

    def broadcast_tx(
        self,
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout: Optional[int] = None,
    ):
        raise RuntimeError("WalletService.broadcast_tx Not implemented yet")

    def is_chain_height_synced_within_tolerance(self) -> bool:
        return self.wallets_setup.is_chain_height_synced_within_tolerance()

    def get_wallet(self) -> "Wallet":
        raise RuntimeError("WalletService.get_wallet Not implemented yet")

    def add_address_confidence_listener(
        self, listener: "AddressConfidenceListener"
    ) -> None:
        raise RuntimeError(
            "WalletService.add_address_confidence_listener Not implemented yet"
        )

    def remove_address_confidence_listener(
        self, listener: "AddressConfidenceListener"
    ) -> None:
        raise RuntimeError(
            "WalletService.remove_address_confidence_listener Not implemented yet"
        )
    
    def add_balance_listener(self, listener: "BalanceListener"):
        self.balance_listeners.add(listener)
    
    def remove_balance_listener(self, listener: "BalanceListener"):
        self.balance_listeners.discard(listener)

    def get_confidence_for_address(self, address: "Address") -> "TransactionConfidence":
        raise RuntimeError("WalletService.get_confidence_for_address Not implemented yet")

    def get_confidence_for_address_from_block_height(
        self, address: "Address", target_height: int
    ) -> "TransactionConfidence":
        raise RuntimeError(
            "WalletService.get_confidence_for_address_from_block_height Not implemented yet"
        )

    def get_balance_for_address(self, address: "Address") -> "Coin":
        raise RuntimeError("WalletService.get_balance_for_address Not implemented yet")
    
    def is_address_unused(self, address: "Address") -> bool:
        raise RuntimeError("BtcWalletService.is_address_unused Not implemented yet")

    @staticmethod
    def maybe_add_network_tx_to_wallet(
        serialized_transaction: bytes, wallet: "Wallet"
    ) -> "Transaction":
        raise RuntimeError(
            "WalletService.maybe_add_network_tx_to_wallet Not implemented yet"
        )

    @staticmethod
    def check_all_script_signatures_for_tx(transaction: "Transaction"):
        raise RuntimeError(
            "WalletService.check_all_script_signatures_for_tx Not implemented yet"
        )

    @staticmethod
    def maybe_add_self_tx_to_wallet(transaction: "Transaction", wallet: "Wallet") -> "Transaction":
        raise RuntimeError(
            "WalletService.maybe_add_self_tx_to_wallet Not implemented yet"
        )

    @staticmethod
    def check_wallet_consistency(wallet: "Wallet"):
        raise RuntimeError("WalletService.check_wallet_consistency Not implemented yet")

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.add_change_event_listener(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.remove_change_event_listener(listener)

    def shut_down(self):
        # TODO
        pass