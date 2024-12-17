from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.script.script import Script
from bitcoinj.script.script_type import ScriptType
from electrum_min.bitcoin import construct_script, opcodes, pubkeyhash_to_p2pkh_script


# NOTE: implement as needed
class ScriptBuilder:
    
    @staticmethod
    def create_output_script(to: Address) -> Script:
        if isinstance(to, SegwitAddress):
            return Script(construct_script([to.witness_version, to.witness_program]))
        elif isinstance(to, LegacyAddress):
            hash_160 = to.bytes
            if to.p2sh:
                return Script(construct_script([opcodes.OP_HASH160, hash_160, opcodes.OP_EQUAL]))
            else:
                return Script(pubkeyhash_to_p2pkh_script(hash_160))
        else:
            raise ValueError(f"Unsupported address type: {type(to)}")