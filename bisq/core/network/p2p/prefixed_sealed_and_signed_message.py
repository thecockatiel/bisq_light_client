from dataclasses import dataclass, field
from typing import ClassVar
import uuid
from bisq.common.crypto.sealed_and_signed import SealedAndSigned
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
import pb_pb2 as protobuf
from utils.data import raise_required


@dataclass
class PrefixedSealedAndSignedMessage(NetworkEnvelope, MailboxMessage, SendersNodeAddressMessage):
    TTL: ClassVar[int] = 15 * 24 * 60 * 60 * 1000  # 15 days in milliseconds

    sender_node_address: NodeAddress = field(default_factory=raise_required)
    sealed_and_signed: SealedAndSigned = field(default_factory=raise_required)
    # From v1.4.0 on addressPrefixHash can be an empty byte array.
    # We cannot make it nullable as not updated nodes would get a nullPointer exception at protobuf serialisation.
    address_prefix_hash: bytes = field(default_factory=lambda: b'')
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        assert self.sender_node_address, "sender_node_address must not be null at PrefixedSealedAndSignedMessage"

    def to_proto_network_envelope(self):
        proto_message = protobuf.PrefixedSealedAndSignedMessage(
            node_address=self.sender_node_address.to_proto_message(),
            sealed_and_signed=self.sealed_and_signed.to_proto_message(),
            address_prefix_hash=self.address_prefix_hash,
            uid=self.uid
        )
        network_envelope = self.get_network_envelope_builder()
        network_envelope.prefixed_sealed_and_signed_message.CopyFrom(proto_message)
        return network_envelope

    @staticmethod
    def from_proto(proto: protobuf.PrefixedSealedAndSignedMessage, message_version: int) -> 'PrefixedSealedAndSignedMessage':
        sender_node_address = NodeAddress.from_proto(proto.node_address)
        sealed_and_signed = SealedAndSigned.from_proto(proto.sealed_and_signed)
        return PrefixedSealedAndSignedMessage(
            sender_node_address=sender_node_address,
            sealed_and_signed=sealed_and_signed,
            address_prefix_hash=proto.address_prefix_hash,
            uid=proto.uid,
            message_version=message_version
        )

    @staticmethod
    def from_payload_proto(proto: protobuf.PrefixedSealedAndSignedMessage) -> 'PrefixedSealedAndSignedMessage':
        # Payloads don't have a message version; set to -1 to indicate it's irrelevant
        sender_node_address = NodeAddress.from_proto(proto.node_address)
        sealed_and_signed = SealedAndSigned.from_proto(proto.sealed_and_signed)
        return PrefixedSealedAndSignedMessage(
            sender_node_address=sender_node_address,
            sealed_and_signed=sealed_and_signed,
            address_prefix_hash=proto.address_prefix_hash,
            uid=proto.uid,
            message_version=-1
        )

    def get_ttl(self) -> int:
        return self.TTL
    
    def __hash__(self):
        return hash((self.sender_node_address, self.sealed_and_signed, self.address_prefix_hash, self.uid))
