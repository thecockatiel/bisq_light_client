from abc import ABC
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.config.config import Config
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.listeners.balance_listener import BalanceListener
from bitcoinj.base.coin import Coin
from bitcoinj.script.script_pattern import ScriptPattern
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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Checks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def check_wallet_consistency(wallet: "Wallet"):
        raise RuntimeError("WalletService.check_wallet_consistency Not implemented yet")

    @staticmethod
    def check_all_script_signatures_for_tx(transaction: "Transaction"):
        raise RuntimeError(
            "WalletService.check_all_script_signatures_for_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Broadcast tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def broadcast_tx(
        self,
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout: Optional[int] = None,
    ):
        raise RuntimeError("WalletService.broadcast_tx Not implemented yet")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TransactionConfidence
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_confidence_for_tx_id(
        self, tx_id: Optional[str]
    ) -> Optional["TransactionConfidence"]:
        raise RuntimeError("WalletService.get_confidence_for_tx_id Not implemented yet")

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

    @property
    def is_chain_height_synced_within_tolerance(self) -> bool:
        return self._wallets_setup.is_chain_height_synced_within_tolerance

    def shut_down(self):
        # TODO
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Balance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_available_balance(self):
        if self.wallet:
            return Coin.value_of(self.wallet.get_available_balance())
        return Coin.ZERO()

    def get_balance_for_address(self, address: "Address") -> "Coin":
        raise RuntimeError("WalletService.get_balance_for_address Not implemented yet")

    def get_tx_fee_for_withdrawal_per_vbyte(self) -> Coin:
        fee = (
            Coin.value_of(self._preferences.get_withdrawal_tx_fee_in_vbytes())
            if self._preferences.get_use_custom_withdrawal_tx_fee()
            else self._fee_service.get_tx_fee_per_vbyte()
        )
        logger.info(f"tx fee = {fee.to_friendly_string()}")
        return fee

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Tx outputs
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_address_unused(self, address: "Address") -> bool:
        raise RuntimeError("BtcWalletService.is_address_unused Not implemented yet")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx_from_serialized_tx(self, tx: bytes) -> Optional["Transaction"]:
        return Transaction(self.params, tx)

    def get_best_chain_height(self) -> int:
        raise RuntimeError("WalletService.get_best_chain_height Not implemented yet")

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

    @property
    def is_wallet_ready(self):
        return self.wallet is not None

    @property
    def is_encrypted(self) -> bool:
        return self.wallet.is_encrypted if self.wallet else False

    @property
    def params(self):
        return self._wallets_setup.params

    @property
    def last_block_seen_height(self) -> int:
        self.wallet.last_block_seen_height

    def get_transactions(self):
        # TODO: original code has a include_dead parameter
        # electrum wallet does not have a concept of dead transactions
        # need to investigate later.
        return self.wallet.get_transactions()

    def get_transaction(
        self, hash_or_tx_id: Union[bytes, Optional[str]]
    ) -> Optional["Transaction"]:
        if hash_or_tx_id is None:
            return None
        if isinstance(hash_or_tx_id, bytes):
            hash_or_tx_id = hash_or_tx_id.hex()
        return self.wallet.get_transaction(hash_or_tx_id)

    def is_transaction_output_mine(
        self, transaction_output: "TransactionOutput"
    ) -> bool:
        return transaction_output.is_for_wallet(self.wallet)

    def find_key_from_pub_key(self, pub_key: bytes) -> "DeterministicKey":
        return self.wallet.find_key_from_pub_key(pub_key)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Util
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def is_output_script_convertible_to_address(
        transaction_output: "TransactionOutput",
    ) -> bool:
        script_pub_key = transaction_output.get_script_pub_key()
        return (
            ScriptPattern.is_p2wpkh(script_pub_key)
            or ScriptPattern.is_p2wsh(script_pub_key)
            or ScriptPattern.is_p2pkh(script_pub_key)
            or ScriptPattern.is_p2sh(script_pub_key)
        )

    @staticmethod
    def get_address_string_from_output(
        transaction_output: "TransactionOutput",
    ) -> Optional[str]:
        if WalletService.is_output_script_convertible_to_address(transaction_output):
            return str(
                transaction_output.get_script_pub_key().get_to_address(
                    Config.BASE_CURRENCY_NETWORK_VALUE.parameters
                )
            )
        return None

    @staticmethod
    def maybe_add_network_tx_to_wallet(
        serialized_transaction: bytes, wallet: "Wallet"
    ) -> "Transaction":
        raise RuntimeError(
            "WalletService.maybe_add_network_tx_to_wallet Not implemented yet"
        )

    @staticmethod
    def maybe_add_self_tx_to_wallet(
        transaction: "Transaction", wallet: "Wallet"
    ) -> "Transaction":
        raise RuntimeError(
            "WalletService.maybe_add_self_tx_to_wallet Not implemented yet"
        )
