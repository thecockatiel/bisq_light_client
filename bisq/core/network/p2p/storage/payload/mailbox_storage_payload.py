from typing import TYPE_CHECKING, Optional, Dict
from dataclasses import dataclass

from bisq.core.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.network.p2p.storage.messages.add_once_payload import AddOncePayload
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload
from bisq.logging import get_logger
from bisq.core.common.crypto.sig import Sig, dsa

import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.network.p2p.prefixed_sealed_and_signed_message import PrefixedSealedAndSignedMessage

logger = get_logger(__name__)

class MailboxStoragePayload(ProtectedStoragePayload, ExpirablePayload, AddOncePayload):
    """
    Payload which supports a time to live and sender and receiver's pub keys for storage operations.\n
    It  differs from the ProtectedExpirableMessage in the way that the sender is permitted to do an add operation
    but only the receiver is permitted to remove the data.\n
    That is the typical requirement for a mailbox like system.\n
    Typical payloads are trade or dispute network_messages to be stored when the peer is offline.\n
    Size depends on payload but typical size is 2000-3000 bytes
    """
    TTL = 15 * 24 * 60 * 60 * 1000  # 15 days in milliseconds

    # Added in 1.5.5
    EXTRA_MAP_KEY_TTL = "ttl"

    def __init__(self,
                 prefixed_sealed_and_signed_message: 'PrefixedSealedAndSignedMessage',
                 sender_pub_key_for_add_operation: 'dsa.DSAPublicKey',
                 owner_pub_key: 'dsa.DSAPublicKey',
                 ttl: int = None,
                 extra_data_map: Optional[Dict[str, str]] = None):
        self.prefixed_sealed_and_signed_message = prefixed_sealed_and_signed_message
        self.sender_pub_key_for_add_operation = sender_pub_key_for_add_operation
        self.owner_pub_key = owner_pub_key

        self.sender_pub_key_for_add_operation_bytes = Sig.get_public_key_bytes(sender_pub_key_for_add_operation)
        self.owner_pub_key_bytes = Sig.get_public_key_bytes(owner_pub_key)

        if ttl:
            # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
            # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
            # field in a class would break that hash and therefore break the storage mechanism.

            # We add optional TTL entry in v 1.5.5 so we can support different TTL for trade messages and for AckMessages

            # We do not permit longer TTL as the default one
            if ttl < self.TTL:
                self.extra_data_map: Optional[Dict[str, str]] = {}
                self.extra_data_map[self.EXTRA_MAP_KEY_TTL] = str(ttl)
            else:
                self.extra_data_map = None

        elif extra_data_map:
            self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(extra_data_map)

    # PROTO BUFFER

    def to_proto_message(self) -> protobuf.StoragePayload:
        payload = protobuf.MailboxStoragePayload()
        payload.prefixed_sealed_and_signed_message.CopyFrom(self.prefixed_sealed_and_signed_message.to_proto_message()) 
        payload.sender_pub_key_for_add_operation_bytes = self.sender_pub_key_for_add_operation_bytes
        payload.owner_pub_key_bytes = self.owner_pub_key_bytes
        if self.extra_data_map:
            payload.extra_data.update(self.extra_data_map)
        return payload

    @staticmethod
    def from_proto(proto: protobuf.MailboxStoragePayload) -> 'MailboxStoragePayload':
        return MailboxStoragePayload(
            PrefixedSealedAndSignedMessage.from_payload_proto(proto.prefixed_sealed_and_signed_message),
            Sig.get_public_key_from_bytes(proto.sender_pub_key_for_add_operation_bytes),
            Sig.get_public_key_from_bytes(proto.owner_pub_key_bytes),
            extra_data_map=proto.extra_data if bool(proto.extra_data) else None
        )

    # API

    def get_ttl(self) -> int:
        if self.extra_data_map and self.EXTRA_MAP_KEY_TTL in self.extra_data_map:
            try:
                ttl = int(self.extra_data_map[self.EXTRA_MAP_KEY_TTL])
                if ttl < self.TTL:
                    return ttl
            except ValueError:
                pass
        # If not set in extra_data_map or value is invalid or too large we return default TTL
        return self.TTL

    def __eq__(self, other):
        if not isinstance(other, MailboxStoragePayload):
            return False
        return (self.prefixed_sealed_and_signed_message == other.prefixed_sealed_and_signed_message and
                self.sender_pub_key_for_add_operation_bytes == other.sender_pub_key_for_add_operation_bytes and
                self.owner_pub_key_bytes == other.owner_pub_key_bytes and
                self.extra_data_map == other.extra_data_map)

    def __hash__(self):
        return hash((self.prefixed_sealed_and_signed_message, self.sender_pub_key_for_add_operation_bytes,
                     self.owner_pub_key_bytes, self.extra_data_map))
