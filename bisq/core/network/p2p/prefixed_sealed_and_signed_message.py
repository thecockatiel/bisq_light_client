from dataclasses import dataclass
from typing import ClassVar
import uuid
import time
from bisq.core.common.crypto.sealed_and_signed import SealedAndSigned
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.senders_node_address_message import SendersNodeAddressMessage
from bisq.logging import get_logger
import bisq.core.common.version as Version
import proto.pb_pb2 as protobuf
import logging

logger =  get_logger(__name__)

@dataclass(frozen=True)
class PrefixedSealedAndSignedMessage(NetworkEnvelope, MailboxMessage, SendersNodeAddressMessage):
    TTL: ClassVar[int] = 15 * 24 * 60 * 60 * 1000  # 15 days in milliseconds

    sender_node_address: NodeAddress
    sealed_and_signed: SealedAndSigned
    # From v1.4.0 on addressPrefixHash can be an empty byte array.
    # We cannot make it nullable as not updated nodes would get a nullPointer exception at protobuf serialisation.
    address_prefix_hash = bytes([])
    uid: str

    def __init__(self, sender_node_address: NodeAddress, sealed_and_signed: SealedAndSigned):
        object.__setattr__(self, 'sender_node_address', sender_node_address)
        object.__setattr__(self, 'sealed_and_signed', sealed_and_signed)
        object.__setattr__(self, 'address_prefix_hash', b'')  # From v1.4.0 on addressPrefixHash can be empty
        object.__setattr__(self, 'uid', str(uuid.uuid4()))
        object.__setattr__(self, 'message_version', Version.get_p2p_message_version())

    def to_proto_network_envelope(self) -> NetworkEnvelope:
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
        return PrefixedSealedAndSignedMessage._private_constructor(
            sender_node_address,
            sealed_and_signed,
            proto.address_prefix_hash,
            proto.uid,
            message_version
        )

    @staticmethod
    def from_payload_proto(proto: protobuf.PrefixedSealedAndSignedMessage) -> 'PrefixedSealedAndSignedMessage':
        # Payloads don't have a message version; set to -1 to indicate it's irrelevant
        sender_node_address = NodeAddress.from_proto(proto.node_address)
        sealed_and_signed = SealedAndSigned.from_proto(proto.sealed_and_signed)
        return PrefixedSealedAndSignedMessage._private_constructor(
            sender_node_address,
            sealed_and_signed,
            proto.address_prefix_hash,
            proto.uid,
            -1
        )

    @staticmethod
    def _private_constructor(sender_node_address: NodeAddress,
                             sealed_and_signed: SealedAndSigned,
                             address_prefix_hash: bytes,
                             uid: str,
                             message_version: int) -> 'PrefixedSealedAndSignedMessage':
        instance = PrefixedSealedAndSignedMessage.__new__(PrefixedSealedAndSignedMessage)
        object.__setattr__(instance, 'sender_node_address', sender_node_address)
        object.__setattr__(instance, 'sealed_and_signed', sealed_and_signed)
        object.__setattr__(instance, 'address_prefix_hash', address_prefix_hash)
        object.__setattr__(instance, 'uid', uid)
        object.__setattr__(instance, 'message_version', message_version)
        return instance

    def get_ttl(self) -> int:
        return self.TTL