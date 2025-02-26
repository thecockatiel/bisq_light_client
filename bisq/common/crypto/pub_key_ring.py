import base64
from dataclasses import dataclass, field

from bisq.common.crypto.encryption import Encryption
from bisq.common.crypto.sig import Sig, DSA
from cryptography.hazmat.primitives.asymmetric import rsa
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
import pb_pb2 as protobuf
from utils.java_compat import java_arrays_byte_hashcode
class PubKeyRing:
    """
    Same as KeyRing but with public keys only.
    Used to send public keys over the wire to other peer.
    """
    signature_pub_key_bytes: bytes
    encryption_pub_key_bytes: bytes

    def __init__(self, signature_pub_key: DSA.DsaKey = None, encryption_pub_key: rsa.RSAPublicKey = None, signature_pub_key_bytes: bytes = None, encryption_pub_key_bytes: bytes = None):
        if (signature_pub_key is not None and encryption_pub_key is not None):
            # Both keys are provided
            pass
        elif (signature_pub_key_bytes is not None and encryption_pub_key_bytes is not None):
            # Both key bytes are provided
            pass
        else:
            raise IllegalArgumentException("Either signature_pub_key and encryption_pub_key or signature_pub_key_bytes and encryption_pub_key_bytes must be provided.")
        
        self._signature_pub_key = signature_pub_key
        self._encryption_pub_key = encryption_pub_key
        self._signature_pub_key_bytes = signature_pub_key_bytes
        self._encryption_pub_key_bytes = encryption_pub_key_bytes

    @property
    def signature_pub_key(self) -> DSA.DsaKey:
        if self._signature_pub_key is None:
            self._signature_pub_key = Sig.get_public_key_from_bytes(self._signature_pub_key_bytes)
        return self._signature_pub_key

    @property
    def encryption_pub_key(self) -> rsa.RSAPublicKey:
        if self._encryption_pub_key is None:
            self._encryption_pub_key = Encryption.get_public_key_from_bytes(self._encryption_pub_key_bytes)
        return self._encryption_pub_key
    
    @property
    def signature_pub_key_bytes(self) -> bytes:
        if self._signature_pub_key_bytes is None:
            self._signature_pub_key_bytes = Sig.get_public_key_bytes(self._signature_pub_key)
        return self._signature_pub_key_bytes
    
    @property
    def encryption_pub_key_bytes(self) -> bytes:
        if self._encryption_pub_key_bytes is None:
            self._encryption_pub_key_bytes = Encryption.get_public_key_bytes(self._encryption_pub_key)
        return self._encryption_pub_key_bytes
    
    def to_proto_message(self):
        return protobuf.PubKeyRing(
            signature_pub_key_bytes=self.signature_pub_key_bytes,
            encryption_pub_key_bytes=self.encryption_pub_key_bytes
        )

    @staticmethod
    def from_proto(proto: protobuf.PubKeyRing):
        return PubKeyRing(
            signature_pub_key_bytes=proto.signature_pub_key_bytes,
            encryption_pub_key_bytes=proto.encryption_pub_key_bytes
        )

    def __str__(self):
        return f"PubKeyRing{{signaturePubKeyHex={self.signature_pub_key_bytes.hex()}" \
               f", encryptionPubKeyHex={self.encryption_pub_key_bytes.hex()}}}"

    def __eq__(self, other):
        return isinstance(other, PubKeyRing) and self.signature_pub_key_bytes == other.signature_pub_key_bytes and self.encryption_pub_key_bytes == other.encryption_pub_key_bytes
    
    def __hash__(self) -> int:
        # lombok's generated hash function for this object
        result = (1 * 59) + java_arrays_byte_hashcode(self.signature_pub_key_bytes)
        return (result * 59) + java_arrays_byte_hashcode(self.encryption_pub_key_bytes)