from typing import TYPE_CHECKING
from electrum_min.transaction import (
    SCRIPTPUBKEY_TEMPLATE_P2PKH,
    SCRIPTPUBKEY_TEMPLATE_P2SH,
    SCRIPTPUBKEY_TEMPLATE_P2WPKH,
    SCRIPTPUBKEY_TEMPLATE_P2WSH,
    SCRIPTPUBKEY_TEMPLATE_WITNESS_V0,
    match_script_against_template,
)

if TYPE_CHECKING:
    from bitcoinj.script.script import Script


class ScriptPattern:

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
        if match_script_against_template(script.decoded, SCRIPTPUBKEY_TEMPLATE_WITNESS_V0):
            return True
        return False
