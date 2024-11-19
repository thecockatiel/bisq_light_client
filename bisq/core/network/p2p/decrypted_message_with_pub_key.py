
from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.crypto.sig import Sig, dsa
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope

class DecryptedMessageWithPubKey(PersistablePayload):
    def __init__(self, network_envelope: 'NetworkEnvelope', signature_pub_key: dsa.DSAPublicKey = None, signature_pub_key_bytes: bytes = None):
        self.network_envelope = network_envelope
        if signature_pub_key is not None:
            self.signature_pub_key = signature_pub_key
            self.signature_pub_key_bytes = Sig.get_public_key_bytes(signature_pub_key)
        elif signature_pub_key_bytes is not None:
            self.signature_pub_key_bytes = signature_pub_key_bytes
            self.signature_pub_key = Sig.get_public_key_from_bytes(signature_pub_key_bytes)
        else:
            raise ValueError("Either signature_pub_key or signature_pub_key_bytes must be provided.")

    def to_proto_message(self) -> protobuf.DecryptedMessageWithPubKey:
        return protobuf.DecryptedMessageWithPubKey(
            network_envelope=self.network_envelope.to_proto_network_envelope(),
            signature_pub_key_bytes=self.signature_pub_key_bytes,
        )

    @staticmethod
    def from_proto(proto: protobuf.DecryptedMessageWithPubKey, network_proto_resolver: 'NetworkProtoResolver') -> 'DecryptedMessageWithPubKey':
        return DecryptedMessageWithPubKey(
            network_envelope=network_proto_resolver.from_proto(proto.network_envelope),
            signature_pub_key_bytes=proto.signature_pub_key_bytes,
        )
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DecryptedMessageWithPubKey):
            return False
        return self.network_envelope == other.network_envelope and self.signature_pub_key_bytes == other.signature_pub_key_bytes
