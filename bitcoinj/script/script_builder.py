from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.crypto.ec_utils import is_compressed_pubkey
from bitcoinj.crypto.transaction_signature import TransactionSignature
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
                return ScriptBuilder.create_p2sh_output_script(to.hash)
            elif script_type == ScriptType.P2PKH:
                return ScriptBuilder.create_p2pkh_output_script(to.hash)
            else:
                raise IllegalStateException(f"Cannot handle {script_type!r}")
        else:
            raise IllegalStateException(f"Unsupported address type: {type(to)}")

    @staticmethod
    def create_p2pkh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a scriptPubKey that sends to the given public key hash. hash160(pubkey)"""
        return Script(bytes.fromhex(pubkeyhash_to_p2pkh_script(pub_key_hash)))

    @staticmethod
    def create_p2wpkh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a segwit scriptPubKey that sends to the given public key hash. hash160(pubkey)"""
        check_argument(
            len(pub_key_hash) == SegwitAddress.WITNESS_PROGRAM_LENGTH_PKH,
            f"pub_key_hash must be {SegwitAddress.WITNESS_PROGRAM_LENGTH_PKH} bytes (hash160)"
        )
        return Script(bytes.fromhex(construct_script([0, pub_key_hash])))

    @staticmethod
    def create_p2pk_output_script(pub_key: bytes) -> Script:
        """Creates a scriptPubKey that encodes payment to the given raw public key."""
        return Script(bytes.fromhex(public_key_to_p2pk_script(pub_key)))

    @staticmethod
    def create_p2sh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a scriptPubKey that sends to the given script hash."""
        check_argument(len(pub_key_hash) == 20, "pub_key_hash must be 20 bytes (hash160)")
        return Script(
            bytes.fromhex(
                construct_script([opcodes.OP_HASH160, pub_key_hash, opcodes.OP_EQUAL])
            )
        )
    
    @staticmethod
    def create_p2wsh_output_script(pub_key_hash: bytes) -> Script:
        """Creates a segwit scriptPubKey that sends to the given script hash. sha256(redeem_script.program)"""
        check_argument(len(pub_key_hash) == 32, "pub_key_hash must be 32 bytes (sha256)")
        return Script(
            bytes.fromhex(
                construct_script([0, pub_key_hash])
            )
        )

    @staticmethod
    def create_op_return_script(data: bytes):
        check_argument(len(data) <= 80, "Data must be <= 80 bytes")
        return Script(bytes.fromhex(construct_script([opcodes.OP_RETURN, data])))
    
    @staticmethod
    def create_p2pkh_input_script(
        signature: TransactionSignature, pub_key_bytes: bytes
    ) -> Script:
        """
        Creates a scriptSig that can redeem a P2PKH output.
        If given signature is null, incomplete scriptSig will be created with OP_0 instead of signature
        """
        sig_bytes = signature.encode_to_bitcoin() if signature is not None else b""
        return Script(
            bytes.fromhex(
                construct_script([sig_bytes, pub_key_bytes])
            )
        )
    
    @staticmethod
    def create_p2pk_input_script(
        signature: TransactionSignature
    ) -> Script:
        """
        Creates a scriptSig that can redeem a P2PK output. If given signature is null, incomplete scriptSig will be created with OP_0 instead of signature
        """
        sig_bytes = signature.encode_to_bitcoin() if signature is not None else b""
        return Script(
            bytes.fromhex(
                construct_script([sig_bytes])
            )
        )