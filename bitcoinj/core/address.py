from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union
from bitcoinj.core.address_format_exception import AddressFormatException
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.script.script_type import ScriptType
from electrum_min.bitcoin import b58_address_to_hash160
from electrum_min.segwit_addr import decode_segwit_address

if TYPE_CHECKING:
    from bisq.common.crypto.encryption import ECPubkey, ECPrivkey
    from bitcoinj.crypto.deterministic_key import DeterministicKey

#NOTE: Implement as necessary
class Address(ABC):
    
    def __init__(self, params: NetworkParameters, bytes_: bytes):
        self.bytes = bytes_
        self.params = params
        
    @staticmethod
    def from_string(addr: str, network_parameters: NetworkParameters=None):
        from bitcoinj.core.legacy_address import LegacyAddress
        from bitcoinj.core.segwit_address import SegwitAddress
        try:
            return LegacyAddress.from_base58(addr, network_parameters)
        except AddressFormatException.WrongNetwork as e:
            raise e
        except Exception as e:
            try:
                return SegwitAddress.from_bech32(addr, network_parameters)
            except Exception as e:
                raise e
        
    @staticmethod
    def from_key(key: Union["ECPrivkey", "ECPubkey", "DeterministicKey"], script_type: "ScriptType", network_parameters: NetworkParameters=None):
        from bitcoinj.core.legacy_address import LegacyAddress
        from bitcoinj.core.segwit_address import SegwitAddress
        
        if script_type == ScriptType.P2PKH:
            return LegacyAddress.from_key(key, network_parameters)
        elif script_type == ScriptType.P2WPKH:
            return SegwitAddress.from_key(key, network_parameters)
        else:
            raise ValueError(f"Unsupported script type: {script_type}")
    
    @staticmethod
    def is_b58_address(addr: str, network_parameters: NetworkParameters=None) -> bool:
        # a slightly modified version of electrum's, to work with bitcoinj style NetworkParameters:
        if network_parameters is None: network_parameters = MainNetParams()
        try:
            # test length, checksum, encoding:
            addrtype, h = b58_address_to_hash160(addr)
        except Exception as e:
            return False
        if addrtype not in [network_parameters.address_header, network_parameters.p2sh_header]:
            return False
        return True
    
    @staticmethod
    def is_segwit_address(addr: str, network_parameters: NetworkParameters=None) -> bool:
        if network_parameters is None: network_parameters = MainNetParams()
        try:
            witver, witprog = decode_segwit_address(network_parameters.segwit_address_hrp, addr)
        except Exception as e:
            return False
        return witprog is not None
    
    @property
    @abstractmethod
    def hash(self) -> bytes:
        """Get either the public key hash or script hash that is encoded in the address."""
        pass
    
    @property
    @abstractmethod
    def output_script_type(self) -> "ScriptType":
        """Get the type of output script that will be used for sending to the address."""
        pass
    