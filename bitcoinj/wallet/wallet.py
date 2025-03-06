from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction import Transaction
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType
from electrum_min.network import Network
from electrum_min.util import EventListener, InvalidPassword, event_listener
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from electrum_min.wallet import Abstract_Wallet
    from bitcoinj.wallet.listeners.wallet_change_event_listener import (
        WalletChangeEventListener,
    )


# TODO implement as needed
class Wallet(EventListener):

    def __init__(
        self, electrum_wallet: "Abstract_Wallet", network_params: "NetworkParameters"
    ):
        self._electrum_wallet = electrum_wallet
        self._network_params = network_params
        self._change_listeners = ThreadSafeSet["WalletChangeEventListener"]()
        self._registered_for_callbacks = False
        self._tx_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self.register_electrum_callbacks()

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
            for listener in self._change_listeners:
                listener.on_wallet_changed(self)

    @event_listener
    def on_event_new_transaction(self, wallet, tx):
        if self._electrum_wallet == wallet:
            for listener in self._change_listeners:
                listener.on_wallet_changed(self)

            if self._tx_listeners:
                wrapped_tx = Transaction.from_electrum_tx(self._network_params, tx)
                for listener in self._tx_listeners:
                    listener(wrapped_tx)

    @event_listener
    def on_event_removed_transaction(self, wallet, tx):
        if self._electrum_wallet == wallet:
            for listener in self._change_listeners:
                listener.on_wallet_changed(self)

    @event_listener
    def on_event_wallet_updated(self, wallet):
        if self._electrum_wallet == wallet:
            for listener in self._change_listeners:
                listener.on_wallet_changed(self)

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
            address = str(LegacyAddress.from_pub_key_hash(pub_key_hash, self._network_params))
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
        return self.find_key_from_pub_key_hash(get_sha256_ripemd160_hash(pub_key), script_type)

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

    def add_tx_listener(self, listener: Callable[["Transaction"], None]):
        self._tx_listeners.add(listener)

    def remove_tx_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._tx_listeners:
            self._tx_listeners.discard(listener)
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

    def start_network(self, network: "Network"):
        return self._electrum_wallet.start_network(network)

    def get_balances(self):
        """returns a set of balances for display purposes: confirmed and matured, unconfirmed, unmatured"""
        return self._electrum_wallet.get_balance()

    def get_available_balance(self) -> int:
        # see https://github.com/spesmilo/electrum/issues/8835
        return sum(utxo.value_sats() for utxo in self._electrum_wallet.get_spendable_coins())

    def get_issued_receive_addresses(self) -> list["Address"]:
        return [
            Address.from_string(address, self._network_params)
            for address in self._electrum_wallet.get_addresses()
        ]

    def is_mine(self, address: str):
        return self._electrum_wallet.is_mine(address)
