from typing import TYPE_CHECKING, Any, Optional

from bitcoinj.base.coin import Coin
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.script.script_type import ScriptType
from bitcoinj.script.script_verify_flag import ScriptVerifyFlag
from electrum_min.bitcoin import opcodes
from electrum_min.transaction import (
    MalformedBitcoinScript,
    OPPushDataGeneric,
    match_script_against_template,
    script_GetOp,
)

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.address import Address
    from bitcoinj.core.network_parameters import NetworkParameters


# TODO
class Script:
    ALL_VERIFY_FLAGS = set([
        ScriptVerifyFlag.P2SH,
        ScriptVerifyFlag.STRICTENC,
        ScriptVerifyFlag.DERSIG,
        ScriptVerifyFlag.LOW_S,
        ScriptVerifyFlag.NULLDUMMY,
        ScriptVerifyFlag.SIGPUSHONLY,
        ScriptVerifyFlag.MINIMALDATA,
        ScriptVerifyFlag.DISCOURAGE_UPGRADABLE_NOPS,
        ScriptVerifyFlag.CLEANSTACK,
        ScriptVerifyFlag.CHECKLOCKTIMEVERIFY,
        ScriptVerifyFlag.CHECKSEQUENCEVERIFY,
    ])

    def __init__(self, program_bytes: Optional[bytes] = None):
        self.program = program_bytes or bytes()
        self.address = None
        self._decoded: Optional[list[tuple[int, bytes | None, int | Any]]] = None
        
    @property
    def decoded(self):
        if self._decoded is None:
            self._decoded = [x for x in script_GetOp(self.program)]
        return self._decoded

    def hex(self) -> str:
        return self.program.hex()

    def get_to_address(self, params: "NetworkParameters") -> "Address":
        # p2pkh
        if ScriptPattern.is_p2pkh(self):
            return LegacyAddress(params, False, self.decoded[2][1])

        # p2sh
        if ScriptPattern.is_p2sh(self):
            return LegacyAddress(params, True, self.decoded[1][1])

        # segwit address (version 0)
        if ScriptPattern.is_witness_v0(self):
            return SegwitAddress.from_hash(self.decoded[1][1], params, 0)

        # segwit address (version 1-16)
        future_witness_versions = list(range(opcodes.OP_1, opcodes.OP_16 + 1))
        for witver, opcode in enumerate(future_witness_versions, start=1):
            match = [opcode, OPPushDataGeneric(lambda x: 2 <= x <= 40)]
            if match_script_against_template(self.decoded, match):
                return SegwitAddress.from_hash(self.decoded[1][1], params, witver)

        return MalformedBitcoinScript("Unknown script type")

    def get_script_type(self) -> Optional["ScriptType"]:
        if ScriptPattern.is_p2pkh(self):
            return ScriptType.P2PKH
        elif ScriptPattern.is_p2sh(self):
            return ScriptType.P2SH
        elif ScriptPattern.is_p2wpkh(self):
            return ScriptType.P2WPKH
        elif ScriptPattern.is_p2wsh(self):
            return ScriptType.P2WSH
        else:
            return None
