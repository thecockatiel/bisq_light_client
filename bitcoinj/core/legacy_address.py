
from typing import Union
from bisq.common.crypto.encryption import Encryption, ECPubkey, ECPrivkey
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bitcoinj.core.address import Address
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.networks import NETWORKS
from bitcoinj.core.address_format_exception import AddressFormatException
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType
from electrum_min.bitcoin import b58_address_to_hash160, hash160_to_b58_address

# NOTE: doesn't cover all methods and properties of the original class, but it should be enough
class LegacyAddress(Address):
    # An address is a RIPEMD160 hash of a public key, therefore is always 160 bits or 20 bytes.
    LENGTH = 20
    
    def __init__(self, params: "NetworkParameters", p2sh: bool, hash160: bytes):
        super().__init__(params, hash160)
        if len(hash160) != LegacyAddress.LENGTH:
            raise ValueError(f"Legacy address hash160 is not 160 bits: {len(hash160)}")
        self.p2sh = p2sh
        """True if P2SH, false if P2PKH."""
        self._str = None
        
    
    @staticmethod
    def from_base58(base58: str, params: "NetworkParameters" = None) -> "LegacyAddress":
        addrtype, hash160 = b58_address_to_hash160(base58)
        p2sh = None
        if params is None:
            for network in NETWORKS:
                if addrtype == network.address_header:
                    p2sh = False
                    break
                if addrtype == network.p2sh_header:
                    p2sh = True
                    break
            if p2sh is None:
                raise AddressFormatException.InvalidPrefix(f"No network found for {base58}")
        else:
            if addrtype == params.address_header:
                p2sh = False
            elif addrtype == params.p2sh_header:
                p2sh = True
            else:
                raise AddressFormatException.WrongNetwork(version_header=addrtype)
        
        return LegacyAddress(params, p2sh, hash160)
    
    @staticmethod
    def from_pub_key_hash(hash160: bytes, params: "NetworkParameters") -> "LegacyAddress":
        return LegacyAddress(params, False, hash160)
    
    @staticmethod
    def from_key(key: Union["ECPrivkey", "ECPubkey", "DeterministicKey"], params: "NetworkParameters") -> "LegacyAddress":
        if isinstance(key, DeterministicKey):
            key_hash = key.get_pub_key_hash()
        else:
            key_hash = get_sha256_ripemd160_hash(Encryption.get_public_key_bytes(key))
        return LegacyAddress.from_pub_key_hash(key_hash, params)
    
    @property
    def version(self) -> int:
        """Get the version header of an address. This is the first byte of a base58 encoded address."""
        if self.p2sh:
            return self.params.p2sh_header
        return self.params.address_header
    
    def to_base58(self):
        """Returns the base58-encoded textual form, including version and checksum bytes."""
        return hash160_to_b58_address(self.bytes, self.version)

    @property
    def hash(self):
        """The (big endian) 20 byte hash that is the core of a Bitcoin address"""
        return self.bytes
    
    @property
    def output_script_type(self):
        if self.p2sh:
            return ScriptType.P2SH
        return ScriptType.P2PKH
    
    def __str__(self):
        if self._str is None:
            self._str = self.to_base58()
        return self._str
    
    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, LegacyAddress):
            return self.bytes == other.bytes and self.p2sh == other.p2sh and self.params == other.params
        return False
    
    def __hash__(self):
        return hash((self.params, self.bytes, self.p2sh))