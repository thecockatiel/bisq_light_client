from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.crypto.ec_utils import is_compressed_pubkey
from bitcoinj.script.script import Script
from bitcoinj.script.script_type import ScriptType
from electrum_min.bitcoin import (
    construct_script,
    opcodes,
    pubkeyhash_to_p2pkh_script,
    public_key_to_p2pk_script,
)
from electrum_min.crypto import hash_160
from utils.preconditions import check_argument


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
            script_type = to.output_script_type
            if script_type == ScriptType.P2SH:
                return Script(
                    bytes.fromhex(
                        construct_script(
                            [opcodes.OP_HASH160, to.hash, opcodes.OP_EQUAL]
                        )
                    )
                )
            elif script_type == ScriptType.P2PKH:
                return ScriptBuilder.create_p2pkh_output_script(to.hash)
            else:
                raise IllegalStateException(f"Cannot handle {script_type!r}")
        else:
            raise IllegalStateException(f"Unsupported address type: {type(to)}")

    @staticmethod
    def create_p2pkh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a scriptPubKey that sends to the given public key."""
        return Script(bytes.fromhex(pubkeyhash_to_p2pkh_script(pub_key_hash)))

    @staticmethod
    def create_p2wpkh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a segwit scriptPubKey that sends to the given public key hash."""
        return Script(bytes.fromhex(construct_script([0, pub_key_hash])))

    @staticmethod
    def create_p2pk_output_script(pub_key: bytes) -> Script:
        """Creates a scriptPubKey that encodes payment to the given raw public key."""
        return Script(bytes.fromhex(public_key_to_p2pk_script(pub_key)))

    @staticmethod
    def create_op_return_script(data: bytes):
        check_argument(len(data) <= 80, "Data must be <= 80 bytes")
        return Script(bytes.fromhex(construct_script([opcodes.OP_RETURN, data])))
