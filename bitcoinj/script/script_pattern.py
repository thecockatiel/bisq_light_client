from typing import TYPE_CHECKING
from bitcoinj.script.script_chunk import is_opcode
from bitcoinj.script.script_utils import ScriptUtils
from electrum_min.bitcoin import opcodes
from electrum_min.transaction import (
    SCRIPTPUBKEY_TEMPLATE_P2PK,
    SCRIPTPUBKEY_TEMPLATE_P2PKH,
    SCRIPTPUBKEY_TEMPLATE_P2SH,
    SCRIPTPUBKEY_TEMPLATE_P2WH,
    SCRIPTPUBKEY_TEMPLATE_P2WPKH,
    SCRIPTPUBKEY_TEMPLATE_P2WSH,
    SCRIPTPUBKEY_TEMPLATE_WITNESS_V0,
    match_script_against_template,
)

if TYPE_CHECKING:
    from bitcoinj.script.script import Script


class ScriptPattern:

    @staticmethod
    def is_p2pk(script: "Script") -> bool:
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_P2PK):
            return True
        return False

    @staticmethod
    def is_p2pkh(script: "Script") -> bool:
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_P2PKH):
            return True
        return False

    @staticmethod
    def is_p2sh(script: "Script") -> bool:
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_P2SH):
            return True
        return False
    
    @staticmethod
    def is_p2wh(script: "Script") -> bool:
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_P2WH):
            return True
        return False

    @staticmethod
    def is_p2wpkh(script: "Script") -> bool:
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_P2WPKH):
            return True
        return False

    @staticmethod
    def is_p2wsh(script: "Script") -> bool:
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_P2WSH):
            return True
        return False

    @staticmethod
    def is_witness_v0(script: "Script") -> bool:
        if match_script_against_template(
            script.decoded, SCRIPTPUBKEY_TEMPLATE_WITNESS_V0
        ):
            return True
        return False

    @staticmethod
    def is_sent_to_multi_sig(script: "Script") -> bool:
        chunks = script.decoded
        if len(chunks) < 4:
            return False
        chunk = chunks[-1]
        # Must end in OP_CHECKMULTISIG[VERIFY].
        if not is_opcode(chunk[0]):
            return False
        if not (
            chunk[0] == opcodes.OP_CHECKMULTISIG
            or chunk[0] == opcodes.OP_CHECKMULTISIGVERIFY
        ):
            return False
        try:
            # Second to last chunk must be an OP_N opcode and there should be that many data chunks (keys).
            m = chunks[-2]
            if not is_opcode(m[0]):
                return False
            num_keys = ScriptUtils.decode_from_op_n(m[0])
            if num_keys < 1 or len(chunks) != 3 + num_keys:
                return False
            for i in range(1, len(chunks) - 2):
                if is_opcode(chunks[i][0]):
                    return False
            # First chunk must be an OP_N opcode too.
            if ScriptUtils.decode_from_op_n(chunks[0][0]) < 1:
                return False
        except:
            return False  # Not an OP_N opcode.

        return True

    @staticmethod
    def is_op_return(script: "Script"):
        """Returns whether this script is using OP_RETURN to store arbitrary data."""
        chunks = script.decoded
        return len(chunks) > 0 and chunks[0][0] == opcodes.OP_RETURN

    def extract_key_from_p2pk(script: "Script") -> bytes:
        """
        Extract the pubkey from a P2SH scriptPubKey.
        It's important that the script is in the correct form,
        so you will want to guard calls to this method with isP2PK(Script).
        """
        return script.decoded[0][1]

    def extract_hash_from_p2pkh(script: "Script") -> bytes:
        """
        Extract the pubkey hash from a P2PKH scriptPubKey.
        It's important that the script is in the correct form,
        so you will want to guard calls to this method with isP2PKH(Script).
        """
        return script.decoded[2][1]

    def extract_hash_from_p2wpkh(script: "Script") -> bytes:
        """
        Extract the pubkey hash from a P2WPKH or the script hash from a P2WSH scriptPubKey.
        It's important that the script is in the correct form,
        so you will want to guard calls to this method with isP2WH(Script).
        """
        return script.decoded[1][1]
