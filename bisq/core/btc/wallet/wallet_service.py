from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional, Union

from bisq.common.config.config import Config
from bisq.core.btc.exceptions.transaction_verification_exception import (
    TransactionVerificationException,
)
from bisq.core.btc.listeners.tx_confidence_listener import TxConfidenceListener
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.btc.wallet.tx_broadcaster import TxBroadcaster
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_confidence_source import TransactionConfidenceSource
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.script.script import Script
from bitcoinj.script.script_pattern import ScriptPattern
from utils.concurrency import AtomicReference, ThreadSafeSet
from utils.data import SimplePropertyChangeEvent
from bitcoinj.core.transaction import Transaction
from utils.preconditions import check_argument, check_not_none

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
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.transaction_output import TransactionOutput


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
        self.logger = get_ctx_logger(__name__)
        self._wallets_setup = wallets_setup
        self._preferences = preferences
        self._fee_service = fee_service

        self._address_to_matching_tx_set_cache = AtomicReference(
            defaultdict["Address", set["Transaction"]](set)
        )
        self.wallet: Optional["Wallet"] = None
        self.password: Optional[str] = None

        self._address_confidence_listeners = ThreadSafeSet[
            "AddressConfidenceListener"
        ]()
        self._tx_confidence_listeners = ThreadSafeSet["TxConfidenceListener"]()
        self._cache_invalidation_listener = (
            lambda *_: self._address_to_matching_tx_set_cache.set(None)
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lifecycle
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners_to_wallet(self):
        if self.wallet:
            self.wallet.add_change_event_listener(self._cache_invalidation_listener)
            self.wallet.add_tx_changed_listener(self._on_tx_changed)

    def shut_down(self):
        if self.wallet:
            self.wallet.remove_change_event_listener(self._cache_invalidation_listener)
            self.wallet.remove_tx_changed_listener(self._on_tx_changed)
            self.wallet = None
        self._tx_confidence_listeners.clear()
        self._address_confidence_listeners.clear()
        self._address_to_matching_tx_set_cache.set(defaultdict(set))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _on_tx_changed(self, tx: "Transaction"):
        if not self.wallet:
            return

        for listener in self._address_confidence_listeners:
            confidence = self._get_transaction_confidence(tx, listener.address)
            listener.on_transaction_confidence_changed(confidence)

        if self._tx_confidence_listeners:
            confidence = self.get_confidence_for_tx_id(tx.get_tx_id())
            for listener in self._tx_confidence_listeners:
                if tx.get_tx_id() == listener.tx_id:
                    listener.on_transaction_confidence_changed(confidence)

    def add_address_confidence_listener(
        self, listener: "AddressConfidenceListener"
    ) -> None:
        self._address_confidence_listeners.add(listener)
        return lambda: self.remove_address_confidence_listener(listener)

    def remove_address_confidence_listener(
        self, listener: "AddressConfidenceListener"
    ) -> None:
        self._address_confidence_listeners.discard(listener)

    def add_tx_confidence_listener(self, listener: "TxConfidenceListener") -> None:
        self._tx_confidence_listeners.add(listener)
        return lambda: self.remove_tx_confidence_listener(listener)

    def remove_tx_confidence_listener(self, listener: "TxConfidenceListener") -> None:
        self._tx_confidence_listeners.discard(listener)

    def add_balance_listener(self, listener: Callable[[Coin], None]):
        return self.wallet.available_balance_property.add_listener(listener)

    def remove_balance_listener(self, listener: Callable[[Coin], None]):
        if self.wallet:
            self.wallet.available_balance_property.remove_listener(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Checks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def check_wallet_consistency(wallet: "Wallet"):
        # Electrum wallet cannot be inconsistent because of the way it stores transactions (?)
        pass

    @staticmethod
    def verify_transaction(transaction: "Transaction") -> None:
        try:
            Transaction.verify(
                Config.BASE_CURRENCY_NETWORK_VALUE.parameters, transaction
            )
        except Exception as e:
            logger = get_ctx_logger(__name__)
            logger.error(e, exc_info=e)
            raise TransactionVerificationException(e)

    @staticmethod
    def check_all_script_signatures_for_tx(transaction: "Transaction"):
        for i, input in enumerate(transaction.inputs):
            WalletService.check_script_sig(transaction, input, i)

    @staticmethod
    def check_script_sig(
        transaction: "Transaction",
        input: "TransactionInput",
        input_index: int,
    ):
        try:
            input.get_script_sig().correctly_spends(
                transaction,
                input_index,
                input.witness_elements,
                input.get_value(),
                check_not_none(
                    input.connected_output, "input.connected_output must not be None"
                ).get_script_pub_key(),
                Script.ALL_VERIFY_FLAGS,
            )
        except Exception as e:
            logger = get_ctx_logger(__name__)
            logger.error(e, exc_info=e)
            raise TransactionVerificationException(e)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Sign tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Dust
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def verify_non_dust_txo(tx: "Transaction") -> None:
        for txo in tx.outputs:
            value = txo.get_value()
            # OpReturn outputs have value 0
            if value.is_positive():
                check_argument(
                    Restrictions.is_above_dust(value),
                    f"An output value is below dust limit. Transaction={tx}",
                )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Broadcast tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def broadcast_tx(
        self,
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout_sec: float = None,
    ):
        TxBroadcaster.broadcast_tx(self.wallet, tx, callback, timeout_sec)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TransactionConfidence
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_confidence_for_address(
        self, address: "Address"
    ) -> Optional["TransactionConfidence"]:
        # TODO: room for optimization
        transaction_confidence_list = []
        if self.wallet:
            transactions = self._get_address_to_matching_tx_set_multimap().get(address)
            if transactions:
                transaction_confidence_list.extend(
                    self._get_transaction_confidence(tx, address) for tx in transactions
                )
        return self._get_most_recent_confidence(transaction_confidence_list)

    def get_confidence_for_address_from_block_height(
        self, address: "Address", target_height: int
    ) -> Optional["TransactionConfidence"]:
        # TODO: room for optimization
        transaction_confidence_list = []
        if self.wallet:
            transactions = self._get_address_to_matching_tx_set_multimap().get(address)
            if transactions:
                # "acceptable confidence" is either a new (pending) Tx, or a Tx confirmed after target block height
                transaction_confidence_list.extend(
                    confidence
                    for tx in transactions
                    if (confidence := self._get_transaction_confidence(tx, address))
                    and (
                        confidence.confidence_type == TransactionConfidenceType.PENDING
                        or (
                            confidence.confidence_type
                            == TransactionConfidenceType.BUILDING
                            and confidence.appeared_at_chain_height > target_height
                        )
                    )
                )
        return self._get_most_recent_confidence(transaction_confidence_list)

    def _get_address_to_matching_tx_set_multimap(
        self,
    ) -> defaultdict["Address", set["Transaction"]]:
        return self._address_to_matching_tx_set_cache.update_and_get(
            lambda map: (
                map if map else self._compute_address_to_matching_tx_set_multimap()
            )
        )

    def _compute_address_to_matching_tx_set_multimap(
        self,
    ) -> defaultdict["Address", set["Transaction"]]:
        if not self.wallet:
            return defaultdict(set)

        address_to_tx_map = defaultdict(set)

        for tx in self.wallet.get_transactions():
            for address in (
                addr
                for output in self._get_outputs_with_connected_outputs(tx)
                if (addr := WalletService.get_address_from_output(output)) is not None
            ):
                address_to_tx_map[address].add(tx)

        return address_to_tx_map

    def get_confidence_for_tx_id(
        self, tx_id: Optional[str]
    ) -> Optional["TransactionConfidence"]:
        if not self.wallet:
            return None

        return self.wallet.get_confidence_for_tx_id(tx_id)

    def _get_transaction_confidence(
        self, tx: "Transaction", address: "Address"
    ) -> Optional["TransactionConfidence"]:
        self.wallet.add_info_from_wallet(tx)
        transaction_confidence_list = [
            self.get_confidence_for_tx_id(output.parent.get_tx_id())
            for output in self._get_outputs_with_connected_outputs(tx)
            if address and address == self.get_address_from_output(output)
        ]
        return self._get_most_recent_confidence(transaction_confidence_list)

    def _get_outputs_with_connected_outputs(
        self, tx: "Transaction"
    ) -> list["TransactionOutput"]:
        transaction_outputs = list(tx.outputs)
        connected_outputs = []

        # add all connected outputs from any inputs as well
        for transaction_input in tx.inputs:
            transaction_output = transaction_input.connected_output
            if transaction_output:
                connected_outputs.append(transaction_output)

        merged_outputs = transaction_outputs + connected_outputs
        return merged_outputs

    def _get_most_recent_confidence(
        self, transaction_confidence_list: list["TransactionConfidence"]
    ) -> Optional["TransactionConfidence"]:
        transaction_confidence = None
        for confidence in transaction_confidence_list:
            if confidence:
                if (
                    transaction_confidence is None
                    or confidence.confidence_type == TransactionConfidenceType.PENDING
                    or (
                        confidence.confidence_type == TransactionConfidenceType.BUILDING
                        and transaction_confidence.confidence_type
                        == TransactionConfidenceType.BUILDING
                        and confidence.depth < transaction_confidence.depth
                    )
                ):
                    transaction_confidence = confidence
        return transaction_confidence

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Balance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_available_balance(self):
        if self.wallet:
            return Coin.value_of(self.wallet.get_available_balance())
        return Coin.ZERO()

    def get_balance_for_address(self, address: Union["Address", str]) -> "Coin":
        if self.wallet and address:
            return Coin.value_of(self.wallet.get_address_balance(address))
        return Coin.ZERO()

    @abstractmethod
    def is_dust_attack_utxo(output: "TransactionOutput"):
        pass

    def get_tx_fee_for_withdrawal_per_vbyte(self) -> Coin:
        fee = (
            Coin.value_of(self._preferences.get_withdrawal_tx_fee_in_vbytes())
            if self._preferences.get_use_custom_withdrawal_tx_fee()
            else self._fee_service.get_tx_fee_per_vbyte()
        )
        self.logger.info(f"tx fee = {fee.to_friendly_string()}")
        return fee

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Tx outputs
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_address_unused(self, address: Union["Address", str]) -> bool:
        return self.wallet.is_address_unused(address)

    # // BISQ issue #4039: Prevent dust outputs from being created.
    # // Check the outputs of a proposed transaction.  If any are below the dust threshold,
    # // add up the dust, log the details, and return the cumulative dust amount.
    def get_dust(self, proposed_transaction: "Transaction") -> Coin:
        dust = Coin.ZERO()
        for transaction_output in proposed_transaction.outputs:
            if transaction_output.get_value().is_less_than(
                Restrictions.get_min_non_dust_output()
            ):
                dust = dust.add(transaction_output.get_value())
                self.logger.info(f"Dust TXO = {transaction_output}")
        return dust

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx_from_serialized_tx(self, tx: bytes) -> "Transaction":
        return Transaction(self.params, tx)

    def get_best_chain_height(self) -> int:
        return self._wallets_setup.chain_height_property.value

    @property
    def is_chain_height_synced_within_tolerance(self) -> bool:
        return self._wallets_setup.is_chain_height_synced_within_tolerance

    def get_cloned_transaction(self, tx: "Transaction") -> "Transaction":
        return Transaction(self.params, tx.bitcoin_serialize())

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Wallet delegates to avoid direct access to wallet outside the service class
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.wallet.add_change_event_listener(listener)
        return lambda: self.remove_change_event_listener(listener)

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
        return self.wallet.last_block_seen_height

    def is_unconfirmed_transactions_limit_hit(self) -> bool:
        """Check if there are more than 20 unconfirmed transactions in the chain right now."""
        # For published delayed payout transactions we do not receive the tx confidence
        # so we cannot check if it is confirmed so we ignore it for that check. The check is any arbitrarily
        # using a limit of 20, so we don't need to be exact here. Should just reduce the likelihood of issues with
        # the too long chains of unconfirmed transactions.
        return (
            sum(
                1
                for tx in self.get_transactions()
                if tx.lock_time == 0
                and self.wallet.is_transaction_pending(tx.get_tx_id())
            )
            > 20
        )

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
    def print_tx(trade_prefix: str, tx: "Transaction") -> None:
        logger = get_ctx_logger(__name__)
        logger.info(f"\n{trade_prefix}:\n{tx}")

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
    def get_address_from_output(
        transaction_output: "TransactionOutput",
    ) -> Optional["Address"]:
        if WalletService.is_output_script_convertible_to_address(transaction_output):
            return transaction_output.get_script_pub_key().get_to_address(
                Config.BASE_CURRENCY_NETWORK_VALUE.parameters
            )
        return None

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
    def maybe_add_tx_to_wallet(
        transaction_or_bytes: Union[bytes, "Transaction"], wallet: "Wallet"
    ) -> "Transaction":
        if isinstance(transaction_or_bytes, Transaction):
            tx = transaction_or_bytes
        else:
            tx = Transaction(wallet.network_params, transaction_or_bytes)
        tx = wallet.maybe_add_transaction(tx)
        return tx
