from bitcoinj.core.address import Address
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType


# TODO
class Wallet:

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
