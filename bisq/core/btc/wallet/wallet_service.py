from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.exceptions.transaction_verification_exception import (
    TransactionVerificationException,
)
from bitcoinj.base.coin import Coin
from bitcoinj.script.script import Script
from bitcoinj.script.script_pattern import ScriptPattern
from utils.concurrency import ThreadSafeSet
from utils.data import SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bitcoinj.core.transaction_input import TransactionInput
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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lifecycle
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def shut_down(self):
        # TODO
        pass

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

    def add_balance_listener(self, listener: Callable[[Coin], None]):
        return self.wallet.available_balance_property.add_listener(listener)

    def remove_balance_listener(self, listener: Callable[[Coin], None]):
        self.wallet.available_balance_property.remove_listener(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Checks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def check_wallet_consistency(wallet: "Wallet"):
        # Electrum wallet cannot be inconsistent because of the way it stores transactions
        pass

    @staticmethod
    def check_all_script_signatures_for_tx(transaction: "Transaction"):
        for i, input in enumerate(transaction.inputs):
            WalletService.check_script_sig(transaction, input, i)

    @staticmethod
    def check_script_sig(
        transaction: "Transaction", input: "TransactionInput", input_index: int
    ):
        try:
            assert (
                input.connected_output is not None
            ), "input.connected_output must not be None"
            input.get_script_sig().correctly_spends(
                transaction,
                input_index,
                input.witness,
                input.value,
                input.connected_output.script_pub_key,
                Script.ALL_VERIFY_FLAGS,
            )
        except Exception as e:
            logger.error(e, exc_info=e)
            raise TransactionVerificationException(e)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Sign tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Dust
    # ///////////////////////////////////////////////////////////////////////////////////////////

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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Balance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_available_balance(self):
        if self.wallet:
            return Coin.value_of(self.wallet.get_available_balance())
        return Coin.ZERO()

    def get_balance_for_address(self, address: Union["Address", str]) -> "Coin":
        if self.wallet:
            return Coin.value_of(self.wallet.get_address_balance(address))
        return Coin.ZERO()

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

    def is_address_unused(self, address: Union["Address", str]) -> bool:
        return self.wallet.is_address_unused(address)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx_from_serialized_tx(self, tx: bytes) -> Optional["Transaction"]:
        return Transaction(self.params, tx)

    def get_best_chain_height(self) -> int:
        return self._wallets_setup.chain_height_property.value

    @property
    def is_chain_height_synced_within_tolerance(self) -> bool:
        return self._wallets_setup.is_chain_height_synced_within_tolerance

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Wallet delegates to avoid direct access to wallet outside the service class
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.add_change_event_listener(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.remove_change_event_listener(listener)

    def add_new_block_height_listener(
        self, listener: Callable[[SimplePropertyChangeEvent[int]], None]
    ):
        return self._wallets_setup.chain_height_property.add_listener(listener)

    def remove_new_block_height_listener(
        self, listener: Callable[[SimplePropertyChangeEvent[int]], None]
    ):
        self._wallets_setup.chain_height_property.remove_listener(listener)

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
