from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.listeners.balance_listener import BalanceListener
from bitcoinj.base.coin import Coin
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bitcoinj.core.listeners.new_best_block_listener import NewBestBlockListener
    from bitcoinj.crypto.deterministic_key import DeterministicKey
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
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.transaction_output import TransactionOutput

logger = get_logger(__name__)


# TODO
class WalletService(ABC):
    """Abstract base class for BTC and BSQ wallet. Provides all non-trade specific functionality."""

    def __init__(
        self,
        wallets_setup: "WalletsSetup",
        preferences: "Preferences",
        fee_service: "FeeService",
    ):
        super().__init__()
        self._wallets_setup = wallets_setup
        self._preferences = preferences
        self._fee_service = fee_service

        self.wallet: Optional["Wallet"] = None
        self.password: Optional[str] = None
        self._balance_listeners = ThreadSafeSet["BalanceListener"]()

    @property
    def is_wallet_ready(self):
        return self.wallet is not None

    @property
    def is_encrypted(self) -> bool:
        return self.wallet.is_encrypted if self.wallet else False
    
    @property
    def params(self):
        return self._wallets_setup.params

    def get_transaction(self,
        hash_or_tx_id: Union[bytes, Optional[str]]
    ) -> Optional["Transaction"]:
        if hash_or_tx_id is None:
            return None
        if isinstance(hash_or_tx_id, bytes):
            hash_or_tx_id = hash_or_tx_id.hex()
        return self.wallet.get_transaction(hash_or_tx_id)

    def get_tx_from_serialized_tx(self, tx: bytes) -> Optional["Transaction"]:
        return Transaction(self.params, tx)

    def get_confidence_for_tx_id(
        self, tx_id: Optional[str]
    ) -> Optional["TransactionConfidence"]:
        raise RuntimeError("WalletService.get_confidence_for_tx_id Not implemented yet")

    def get_tx_fee_for_withdrawal_per_vbyte(self) -> Coin:
        fee = (
            Coin.value_of(self._preferences.get_withdrawal_tx_fee_in_vbytes())
            if self._preferences.get_use_custom_withdrawal_tx_fee()
            else self._fee_service.get_tx_fee_per_vbyte()
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
        return self._wallets_setup.is_chain_height_synced_within_tolerance()

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
        self._balance_listeners.add(listener)

    def remove_balance_listener(self, listener: "BalanceListener"):
        self._balance_listeners.discard(listener)

    def get_confidence_for_address(self, address: "Address") -> "TransactionConfidence":
        raise RuntimeError(
            "WalletService.get_confidence_for_address Not implemented yet"
        )

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
    def maybe_add_self_tx_to_wallet(
        transaction: "Transaction", wallet: "Wallet"
    ) -> "Transaction":
        raise RuntimeError(
            "WalletService.maybe_add_self_tx_to_wallet Not implemented yet"
        )

    @staticmethod
    def check_wallet_consistency(wallet: "Wallet"):
        raise RuntimeError("WalletService.check_wallet_consistency Not implemented yet")

    def get_best_chain_height(self) -> int:
        raise RuntimeError("WalletService.get_best_chain_height Not implemented yet")

    def shut_down(self):
        # TODO
        pass

    def get_transactions(self, include_dead: bool) -> set["Transaction"]:
        raise RuntimeError("WalletService.get_transactions Not implemented yet")

    def find_key_from_pub_key(self, pub_key: bytes) -> "DeterministicKey":
        raise RuntimeError("WalletService.find_key_from_pub_key Not implemented yet")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Wallet delegates to avoid direct access to wallet outside the service class
    # ///////////////////////////////////////////////////////////////////////////////////////////   

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.add_change_event_listener(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.remove_change_event_listener(listener)

    def add_new_best_block_listener(self, listener: "NewBestBlockListener"):
        pass

    def remove_new_best_block_listener(self, listener: "NewBestBlockListener"):
        pass