from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.crypto.ec_utils import is_compressed_pubkey
from bitcoinj.script.script import Script
from electrum_min.bitcoin import construct_script, opcodes, pubkeyhash_to_p2pkh_script


# NOTE: implement as needed
class ScriptBuilder:

    @staticmethod
    def create_output_script(to: Address) -> Script:
        if isinstance(to, SegwitAddress):
            return Script(
                bytes.fromhex(
                    construct_script([to.witness_version, to.witness_program])
                )
            )
        elif isinstance(to, LegacyAddress):
            hash_160 = to.bytes
            if to.p2sh:
                return Script(
                    bytes.fromhex(
                        construct_script(
                            [opcodes.OP_HASH160, hash_160, opcodes.OP_EQUAL]
                        )
                    )
                )
            else:
                return ScriptBuilder.create_p2pkh_output_script(hash_160)
        else:
            raise ValueError(f"Unsupported address type: {type(to)}")

    @staticmethod
    def create_p2pkh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a scriptPubKey that sends to the given public key."""
        assert is_compressed_pubkey(pub_key_hash), "pubkey was not compressed"
        return Script(bytes.fromhex(pubkeyhash_to_p2pkh_script(pub_key_hash)))
