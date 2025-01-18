from dataclasses import dataclass, field
from typing import Optional 
from bisq.common.crypto.sig import Sig,dsa
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.util.utilities import bytes_as_hex_string
import proto.pb_pb2 as protobuf
from utils.data import raise_required


@dataclass
class PrivateNotificationPayload(NetworkPayload):
    message: str = field(default_factory=raise_required)
    signature_as_base64: Optional[str] = field(default=None)
    sig_public_key_bytes: Optional[bytes] = field(default=None)
    sig_public_key: Optional['dsa.DSAPublicKey'] = field(default=None)
    
    def __post_init__(self):
        if self.sig_public_key_bytes is not None:
            self.sig_public_key = Sig.get_public_key_from_bytes(self.sig_public_key_bytes)
    
    @staticmethod
    def from_proto(proto: protobuf.PrivateNotificationPayload) -> 'PrivateNotificationPayload':
        return PrivateNotificationPayload(
            message=proto.message,
            signature_as_base64=proto.signature_as_base64,
            sig_public_key_bytes=proto.sig_public_key_bytes,
        )

    def to_proto_message(self):
        assert self.sig_public_key_bytes is not None, "sig_public_key_bytes must not be null"
        assert self.signature_as_base64 is not None, "signature_as_base64 must not be null"
        
        return protobuf.PrivateNotificationPayload(
            message=self.message,
            signature_as_base64=self.signature_as_base64,
            sig_public_key_bytes=self.sig_public_key_bytes
        )

    def set_sig_and_pub_key(self, signature_as_base64: str, sig_public_key: dsa.DSAPublicKey):
        self.signature_as_base64 = signature_as_base64
        self.sig_public_key = sig_public_key
        self.sig_public_key_bytes = Sig.get_public_key_bytes(sig_public_key)

    def __str__(self) -> str:
        return (f"PrivateNotification("
                f"message='{self.message}', "
                f"signature_as_base64='{self.signature_as_base64}', "
                f"public_key_bytes={bytes_as_hex_string(self.sig_public_key_bytes)})")