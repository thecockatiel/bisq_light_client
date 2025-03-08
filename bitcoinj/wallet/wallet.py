from collections.abc import Callable
from typing import TYPE_CHECKING, Generator, Optional, Union
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.transaction_confidence import TransactionConfidence
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType
from electrum_min.network import Network
from electrum_min.util import EventListener, InvalidPassword, event_listener
from utils.concurrency import ThreadSafeSet
from utils.data import SimpleProperty

if TYPE_CHECKING:
    from electrum_min.wallet import Abstract_Wallet
    from bitcoinj.wallet.listeners.wallet_change_event_listener import (
        WalletChangeEventListener,
    )


# TODO implement as needed
class Wallet(EventListener):

    def __init__(
        self,
        electrum_wallet: "Abstract_Wallet",
        electrum_network: "Network",
        network_params: "NetworkParameters",
    ):
        self._electrum_wallet = electrum_wallet
        self._electrum_network = electrum_network
        self._network_params = network_params
        self._change_listeners = ThreadSafeSet["WalletChangeEventListener"]()
        self._registered_for_callbacks = False
        self._tx_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self._tx_changed_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self.register_electrum_callbacks()
        self._last_balance = 0
        self._available_balance_property = SimpleProperty(Coin.ZERO())

    @property
    def available_balance_property(self):
        return self._available_balance_property

    # //////////////////////////////////////////////////////////////////////
    # // Electrum bridge
    # //////////////////////////////////////////////////////////////////////

    def register_electrum_callbacks(self):
        if not self._registered_for_callbacks:
            self._registered_for_callbacks = True
            EventListener.register_callbacks(self)

    def unregister_electrum_callbacks(self):
        if self._registered_for_callbacks:
            self._registered_for_callbacks = False
            EventListener.unregister_callbacks(self)

    @event_listener
    def on_event_verified(self, wallet, txid, info):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

            if self._tx_changed_listeners:
                wrapped_tx = self.get_transaction(txid)
                wrapped_tx.add_info_from_wallet(self)
                for listener in self._tx_changed_listeners:
                    listener(wrapped_tx)

    @event_listener
    def on_event_new_transaction(self, wallet, tx):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

            if self._tx_listeners:
                wrapped_tx = Transaction.from_electrum_tx(self._network_params, tx)
                wrapped_tx.add_info_from_wallet(self)
                for listener in self._tx_listeners:
                    listener(wrapped_tx)

            if self._tx_changed_listeners:
                wrapped_tx = Transaction.from_electrum_tx(self._network_params, tx)
                wrapped_tx.add_info_from_wallet(self)
                for listener in self._tx_changed_listeners:
                    listener(wrapped_tx)

    @event_listener
    def on_event_removed_transaction(self, wallet, tx):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

    @event_listener
    def on_event_wallet_updated(self, wallet):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

    def on_wallet_changed(self):
        for listener in self._change_listeners:
            listener.on_wallet_changed(self)
        self._available_balance_property.set(
            Coin.value_of(self.get_available_balance())
        )

    # //////////////////////////////////////////////////////////////////////
    # // Bitcoinj Wallet API
    # //////////////////////////////////////////////////////////////////////

    def find_key_from_address(
        self,
        address: "Address",
    ) -> Optional["DeterministicKey"]:
        script_type = address.output_script_type
        if script_type == ScriptType.P2PKH or script_type == ScriptType.P2WPKH:
            keys = self._electrum_wallet.get_public_keys_with_deriv_info(str(address))
            if keys:
                first_item = next(iter(keys.items()))
                pubkey = first_item[0]
                keystore = first_item[1][0]
                return DeterministicKey(pubkey, keystore)
        return None

    def find_key_from_pub_key_hash(
        self,
        pub_key_hash: bytes,
        script_type: "ScriptType",
    ) -> Optional["DeterministicKey"]:
        if script_type == ScriptType.P2WPKH:
            address = str(SegwitAddress.from_hash(pub_key_hash, self._network_params))
        elif script_type == ScriptType.P2PKH:
            address = str(
                LegacyAddress.from_pub_key_hash(pub_key_hash, self._network_params)
            )
        else:
            return None
        keys = self._electrum_wallet.get_public_keys_with_deriv_info(address)
        if keys:
            first_item = next(iter(keys.items()))
            pubkey = first_item[0]
            keystore = first_item[1][0]
            return DeterministicKey(pubkey, keystore)
        return None

    def find_key_from_pub_key(
        self,
        pub_key: bytes,
        script_type: "ScriptType",
    ) -> Optional["DeterministicKey"]:
        return self.find_key_from_pub_key_hash(
            get_sha256_ripemd160_hash(pub_key), script_type
        )

    def get_receiving_address(self) -> "Address":
        return Address.from_string(
            self._electrum_wallet.get_receiving_address(), self._network_params
        )

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self._change_listeners.add(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        if listener in self._change_listeners:
            self._change_listeners.discard(listener)
            return True
        return False

    def add_new_tx_listener(self, listener: Callable[["Transaction"], None]):
        self._tx_listeners.add(listener)

    def remove_new_tx_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._tx_listeners:
            self._tx_listeners.discard(listener)
            return True
        return False

    def add_tx_changed_listener(self, listener: Callable[["Transaction"], None]):
        self._tx_changed_listeners.add(listener)

    def remove_tx_changed_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._tx_changed_listeners:
            self._tx_changed_listeners.discard(listener)
            return True
        return False

    def decrypt(self, password: str):
        """removes wallet file password"""
        if not self.is_encrypted:
            raise IllegalStateException("Wallet is not encrypted")
        try:
            self._electrum_wallet.update_password(password, None)
        except InvalidPassword:
            raise IllegalArgumentException("Invalid password")

    def encrypt(self, password: str):
        """adds password to wallet file"""
        if self.is_encrypted:
            raise IllegalStateException("Wallet is already encrypted")
        # NOTE: this operation is io blocking, but should be fine
        self._electrum_wallet.update_password(None, password)

    def unlock(self, password: str):
        self._electrum_wallet.unlock(password)

    def lock(self):
        self._electrum_wallet.lock()

    @property
    def is_encrypted(self):
        return self._electrum_wallet.has_storage_encryption()

    @property
    def network_params(self):
        return self._network_params

    def stop(self):
        return self._electrum_wallet.stop()

    def start_network(self):
        return self._electrum_wallet.start_network(self._electrum_network)

    def get_balances(self):
        """returns a set of balances for display purposes: confirmed and matured, unconfirmed, unmatured"""
        return self._electrum_wallet.get_balance()

    def get_available_balance(self) -> int:
        # see https://github.com/spesmilo/electrum/issues/8835
        return sum(
            utxo.value_sats() for utxo in self._electrum_wallet.get_spendable_coins()
        )

    def get_address_balance(self, address: Union["Address", str]) -> int:
        if isinstance(address, Address):
            address = str(address)
        return sum(
            utxo.value_sats()
            for utxo in self._electrum_wallet.get_spendable_coins([address])
        )

    def get_issued_receive_addresses(self) -> list["Address"]:
        return [
            Address.from_string(address, self._network_params)
            for address in self._electrum_wallet.get_addresses()
        ]

    def is_address_unused(self, address: Union["Address", str]):
        if isinstance(address, Address):
            address = str(address)
        return self._electrum_wallet.is_address_unused(address)

    def is_mine(self, address: Union["Address", str]):
        if isinstance(address, Address):
            address = str(address)
        return self._electrum_wallet.is_mine(address)

    def get_transaction(self, txid: str) -> Optional["Transaction"]:
        e_tx = self._electrum_wallet.db.get_transaction(txid)
        if e_tx:
            tx = Transaction.from_electrum_tx(self.network_params, e_tx)
            tx.add_info_from_wallet(self)
            return tx
        return None

    @property
    def last_block_seen_height(self):
        return self._electrum_network.get_local_height()

    def get_transactions(self) -> Generator["Transaction"]:
        """return an Generator that returns all transactions in the wallet, newest first"""
        for tx in reversed(self._electrum_wallet.db.transactions.values()):
            tx = Transaction.from_electrum_tx(self.network_params, tx)
            tx.add_info_from_wallet(self)
            yield tx

    def get_tx_mined_info(self, txid: str):
        return self._electrum_wallet.adb.get_tx_height(txid)
    
    def add_info_from_wallet(self, tx: "Transaction"):
        """populates prev_txs"""
        tx._electrum_transaction.add_info_from_wallet(self._electrum_wallet)
        tx.inputs.invalidate()
        tx.outputs.invalidate()

    def get_label_for_txid(self, txid: str):
        return self._electrum_wallet.get_label_for_txid(txid)

    def maybe_add_transaction(self, tx: "Transaction"):
        """tries to add transaction to history of wallet and may raise error"""
        existing_tx = self._electrum_wallet.db.get_transaction(tx.get_tx_id())
        if existing_tx:
            return Transaction.from_electrum_tx(self.network_params, existing_tx)
        Transaction.verify(Wallet.network_params, tx)
        self._electrum_wallet.adb.add_unverified_or_unconfirmed_tx(tx.get_tx_id(), 0)
        added = self._electrum_wallet.adb.add_transaction(
            tx._electrum_transaction, allow_unrelated=True, is_new=True
        )
        if not added:
            raise VerificationException(
                "Transaction could not be added to wallet history due to conflicts"
            )
        existing_tx = self._electrum_wallet.db.get_transaction(tx.get_tx_id())
        if not existing_tx:
            # unlikely, just in case
            raise IllegalStateException("Transaction was not added to wallet history")
        return Transaction.from_electrum_tx(self.network_params, existing_tx)

    def is_transaction_pending(self, tx_id: str):
        return (
            tx_id in self._electrum_wallet.adb.unconfirmed_tx
            or tx_id in self._electrum_wallet.adb.unverified_tx
        )

    def get_confidence_for_tx_id(
        self, tx_id: Optional[str]
    ) -> Optional["TransactionConfidence"]:
        if not tx_id:
            return None

        info = self.get_tx_mined_info(tx_id)
        if info.conf > 0:
            return TransactionConfidence(
                tx_id,
                depth=self.last_block_seen_height - info.height,
                appeared_at_chain_height=info.height,
                confidence_type=TransactionConfidenceType.BUILDING,
            )
        else:
            is_pending = self.is_transaction_pending(tx_id)
            return TransactionConfidence(
                tx_id,
                depth=0,
                confidence_type=(
                    TransactionConfidenceType.PENDING
                    if is_pending
                    else TransactionConfidenceType.UNKNOWN
                ),
            )
