from typing import TYPE_CHECKING
from bitcoinj.core.address import Address
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bitcoinj.wallet.listeners.wallet_change_event_listener import WalletChangeEventListener

# TODO
class Wallet:
    
    def __init__(self):
        self.change_listeners = ThreadSafeSet["WalletChangeEventListener"]()

    def find_key_from_pub_key_hash(
        self,
        pub_key_hash: bytes,
        script_type: ScriptType,
    ) -> "DeterministicKey":
        raise NotImplementedError("find_key_from_pub_key_hash not implemented yet")

    def find_key_from_address(
        self,
        address: "Address",
    ) -> "DeterministicKey":
        script_type = address.output_script_type
        if script_type == ScriptType.P2PKH or script_type == ScriptType.P2WPKH:
            return self.find_key_from_pub_key_hash(address.hash, script_type)
        return None

    def fresh_receive_address(self, script_type: ScriptType) -> "Address":
        raise NotImplementedError("fresh_receive_address not implemented yet")

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self.change_listeners.add(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        if listener in self.change_listeners:
            self.change_listeners.discard(listener)
            return True
        return False
