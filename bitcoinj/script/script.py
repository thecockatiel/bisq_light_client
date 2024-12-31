from typing import TYPE_CHECKING, Optional

from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.script.script_type import ScriptType
from electrum_min.bitcoin import opcodes
from electrum_min.transaction import (
    SCRIPTPUBKEY_TEMPLATE_P2PKH,
    SCRIPTPUBKEY_TEMPLATE_P2SH,
    SCRIPTPUBKEY_TEMPLATE_P2WPKH,
    SCRIPTPUBKEY_TEMPLATE_P2WSH,
    SCRIPTPUBKEY_TEMPLATE_WITNESS_V0,
    MalformedBitcoinScript,
    OPPushDataGeneric,
    match_script_against_template,
    script_GetOp,
)

if TYPE_CHECKING:
    from bitcoinj.core.address import Address
    from bitcoinj.core.network_parameters import NetworkParameters


# TODO
class Script:

    def __init__(self, program_bytes: Optional[bytes] = None):
        self.program = program_bytes or bytes()
        self.address = None

    def hex(self) -> str:
        return self.program.hex()

    def get_to_address(self, params: "NetworkParameters") -> "Address":
        decoded = [x for x in script_GetOp(self.program)]

        # p2pkh
        if match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_P2PKH):
            return LegacyAddress(params, False, decoded[2][1])

        # p2sh
        if match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_P2SH):
            return LegacyAddress(params, True, decoded[1][1])

        # segwit address (version 0)
        if match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_WITNESS_V0):
            return SegwitAddress.from_hash(decoded[1][1], params, 0)

        # segwit address (version 1-16)
        future_witness_versions = list(range(opcodes.OP_1, opcodes.OP_16 + 1))
        for witver, opcode in enumerate(future_witness_versions, start=1):
            match = [opcode, OPPushDataGeneric(lambda x: 2 <= x <= 40)]
            if match_script_against_template(decoded, match):
                return SegwitAddress.from_hash(decoded[1][1], params, witver)

        return MalformedBitcoinScript("Unknown script type")

    def get_script_type(self) -> Optional["ScriptType"]:
        decoded = [x for x in script_GetOp(self.program)]

        if match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_P2PKH):
            return ScriptType.P2PKH
        elif match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_P2SH):
            return ScriptType.P2SH
        elif match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_P2WPKH):
            return ScriptType.P2WPKH
        elif match_script_against_template(decoded, SCRIPTPUBKEY_TEMPLATE_P2WSH):
            return ScriptType.P2WSH
        else:
            return None
