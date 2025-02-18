from dataclasses import dataclass, field
from typing import Optional 
  
from bisq.common.protocol.network.network_payload import NetworkPayload
import pb_pb2 as protobuf
from bisq.common.crypto.sig import Sig, DSA

class SealedAndSigned(NetworkPayload):
    encrypted_secret_key: bytes
    encrypted_payload_with_hmac: bytes
    signature: bytes
    sig_public_key: Optional['DSA.DsaKey'] = None
    sig_public_key_bytes: Optional[bytes] = None

    def __init__(self, encrypted_secret_key: bytes, encrypted_payload_with_hmac: bytes, signature: bytes, sig_public_key: Optional['DSA.DsaKey'] = None, sig_public_key_bytes: Optional[bytes] = None):
        super().__init__()
        if sig_public_key is not None:
            self.sig_public_key_bytes = Sig.get_public_key_bytes(sig_public_key)
            self.sig_public_key = sig_public_key
        elif sig_public_key_bytes is not None:
            self.sig_public_key = Sig.get_public_key_from_bytes(sig_public_key_bytes)
            self.sig_public_key_bytes = sig_public_key_bytes
        else:
            raise ValueError("Either sig_public_key or sig_public_key_bytes must be provided.")
        self.encrypted_secret_key = encrypted_secret_key
        self.encrypted_payload_with_hmac = encrypted_payload_with_hmac
        self.signature = signature

    @staticmethod
    def from_proto(proto: protobuf.SealedAndSigned) -> 'SealedAndSigned':
        return SealedAndSigned(
            encrypted_secret_key=proto.encrypted_secret_key,
            encrypted_payload_with_hmac=proto.encrypted_payload_with_hmac,
            signature=proto.signature,
            sig_public_key=Sig.get_public_key_from_bytes(proto.sig_public_key_bytes)
        )

    def to_proto_message(self) -> protobuf.SealedAndSigned:
        return protobuf.SealedAndSigned(
            encrypted_secret_key=self.encrypted_secret_key,
            encrypted_payload_with_hmac=self.encrypted_payload_with_hmac,
            signature=self.signature,
            sig_public_key_bytes=self.sig_public_key_bytes
        )

    def __eq__(self, other):
        return isinstance(other, SealedAndSigned) and self.encrypted_secret_key == other.encrypted_secret_key and self.encrypted_payload_with_hmac == other.encrypted_payload_with_hmac and self.signature == other.signature and self.sig_public_key_bytes == other.sig_public_key_bytes
    
    def __hash__(self) -> int:
        return hash((self.encrypted_secret_key, self.encrypted_payload_with_hmac, self.signature, self.sig_public_key_bytes))