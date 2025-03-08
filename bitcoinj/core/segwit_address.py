from typing import Optional, Union
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.core.address import Address
from bitcoinj.core.address_format_exception import AddressFormatException
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.crypto.ec_utils import is_compressed_pubkey
from bitcoinj.script.script_type import ScriptType
from electrum_min.segwit_addr import Encoding, bech32_decode, convertbits, encode_segwit_address
from bisq.common.crypto.encryption import Encryption, ECPubkey, ECPrivkey
from bitcoinj.core.networks import NETWORKS
from utils.preconditions import check_argument, check_state


# NOTE: doesn't cover all methods and properties of the original class, but it should be enough
class SegwitAddress(Address):
    WITNESS_PROGRAM_LENGTH_PKH = 20
    WITNESS_PROGRAM_LENGTH_SH = 32
    WITNESS_PROGRAM_MIN_LENGTH = 2
    WITNESS_PROGRAM_MAX_LENGTH = 40
    
    def __init__(self, params: "NetworkParameters", data: bytes):
        super().__init__(params, data)
        if len(data) < 1:
            raise AddressFormatException.InvalidDataLength("Zero data found")
        witness_version = self.witness_version
        if witness_version < 0 or witness_version > 16:
            AddressFormatException(f"Invalid script version: {witness_version}")
        witness_program = self.witness_program
        if len(witness_program) < SegwitAddress.WITNESS_PROGRAM_MIN_LENGTH or len(witness_program) > SegwitAddress.WITNESS_PROGRAM_MAX_LENGTH:
            raise AddressFormatException.InvalidDataLength(f"Invalid length: {len(witness_program)}")
        # Check script length for version 0
        if witness_version == 0 and len(witness_program) != SegwitAddress.WITNESS_PROGRAM_LENGTH_PKH \
                and len(witness_program) != SegwitAddress.WITNESS_PROGRAM_LENGTH_SH:
            raise AddressFormatException.InvalidDataLength(f"Invalid length for address version 0: {len(witness_program)}")

        self._str = None
            
    @property
    def witness_version(self) -> int:
        """Returns the witness version in decoded form between 0 and 16. Only version 0 is in use right now."""
        return self.bytes[0]
    
    @property
    def witness_program(self) -> bytes:
        """Returns the witness program in decoded form."""
        # skip version byte
        return bytes(convertbits(self.bytes[1:], 5, 8, False))
    
    @property
    def hash(self):
        return self.witness_program
    
    @property
    def output_script_type(self):
        """Get the type of output script that will be used for sending to the address. This is either ScriptType.P2WPKH or ScriptType.P2WSH."""
        version = self.witness_version
        check_state(version == 0)
        program_length = len(self.witness_program)
        if program_length == SegwitAddress.WITNESS_PROGRAM_LENGTH_PKH:
            return ScriptType.P2WPKH
        if program_length == SegwitAddress.WITNESS_PROGRAM_LENGTH_SH:
            return ScriptType.P2WSH
        raise IllegalStateException("Cannot happen.")
    
    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, SegwitAddress):
            return self.params == other.params and self.bytes == other.bytes
        return False
    
    def __hash__(self):
        return hash((self.params, self.bytes))
    
    def __str__(self):
        if self._str is None:
            self._str = self.to_bech32()
        return self._str
    
    def to_bech32(self) -> str:
        """Returns the bech32-encoded textual form."""
        return encode_segwit_address(self.params.segwit_address_hrp, self.witness_version, self.witness_program)
    
    @staticmethod
    def from_bech32(bech32: str, params: Optional["NetworkParameters"] = None) -> "SegwitAddress":
        if not bech32:
            raise AddressFormatException("Invalid bech32 address")
        
        encoding, hrpgot, data = bech32_decode(bech32)
        if data is None:
            raise AddressFormatException("Invalid bech32 address")
        if params is None:
            for network in NETWORKS:
                if network.segwit_address_hrp == hrpgot:
                    params = network
                    break
            raise AddressFormatException.InvalidPrefix(f"No network found for {bech32}")
        else:
            if hrpgot != params.segwit_address_hrp:
                raise AddressFormatException.WrongNetwork(hrp=hrpgot)
        if (data[0] == 0 and encoding != Encoding.BECH32) or (data[0] != 0 and encoding != Encoding.BECH32M):
            raise AddressFormatException("Invalid encoding")
        return SegwitAddress(params, bytes(data))
        
    @staticmethod
    def from_hash(hash: bytes, params: "NetworkParameters", witness_version: int = 0) -> "SegwitAddress":
        """
        Create a SegwitAddress that represents the given hash, which is either a pubkey hash or a script hash.
        
        The resulting address will be either a P2WPKH or a P2WSH type of address.
        
        hash: 20-byte pubkey hash or 32-byte script hash
        """
        return SegwitAddress(params, bytes([witness_version]) + bytes(convertbits(hash, 8, 5, True)))
    
    @staticmethod
    def from_key(key: Union["ECPubkey", "ECPrivkey", "DeterministicKey"], params: "NetworkParameters") -> "SegwitAddress":
        if isinstance(key, DeterministicKey):
            key_hash = key.get_pub_key_hash()
        else:
            check_argument(is_compressed_pubkey(key.get_public_key_bytes()), "only compressed keys allowed")
            key_hash = get_sha256_ripemd160_hash(Encryption.get_public_key_bytes(key))
        return SegwitAddress.from_hash(key_hash, params)
