from typing import TYPE_CHECKING, Optional
from bitcoinj.core.address import Address
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType
from electrum_min.util import EventListener, event_listener
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from electrum_min.wallet import Abstract_Wallet
    from bitcoinj.wallet.listeners.wallet_change_event_listener import WalletChangeEventListener

# TODO implement as needed
class Wallet:
    
    def __init__(self, electrum_wallet: "Abstract_Wallet", network: "NetworkParameters"):
        self._electrum_wallet = electrum_wallet
        self._network = network
        self._change_listeners = ThreadSafeSet["WalletChangeEventListener"]()
        self._registered_for_callbacks = False
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

    def get_receiving_address(self) -> "Address":
        return Address.from_string(self._electrum_wallet.get_receiving_address(), self._network)

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self._change_listeners.add(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        if listener in self._change_listeners:
            self._change_listeners.discard(listener)
            return True
        return False
