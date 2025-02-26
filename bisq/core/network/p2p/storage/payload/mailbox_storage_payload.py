from datetime import timedelta
from typing import Optional

from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.network.p2p.storage.messages.add_once_payload import AddOncePayload
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload
from bisq.common.setup.log_setup import get_logger
from bisq.common.crypto.sig import Sig, DSA
from bisq.core.network.p2p.prefixed_sealed_and_signed_message import PrefixedSealedAndSignedMessage

import pb_pb2 as protobuf

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
    TTL = int(timedelta(days=15).total_seconds()*1000)  # 15 days in milliseconds

    # Added in 1.5.5
    EXTRA_MAP_KEY_TTL = "ttl"

    def __init__(
            self,
            prefixed_sealed_and_signed_message: 'PrefixedSealedAndSignedMessage',
            ttl: int = None,
            extra_data_map: Optional[dict[str, str]] = None,
            sender_pub_key_for_add_operation: 'DSA.DsaKey' = None,
            owner_pub_key: 'DSA.DsaKey' = None,
            sender_pub_key_for_add_operation_bytes: bytes = None,
            owner_pub_key_bytes: bytes = None,
        ):
        self.prefixed_sealed_and_signed_message = prefixed_sealed_and_signed_message

        if (owner_pub_key is not None and sender_pub_key_for_add_operation is not None):
            # Both keys are provided
            pass
        elif (sender_pub_key_for_add_operation_bytes is not None and owner_pub_key_bytes is not None):
            # Both key bytes are provided
            pass
        else:
            raise IllegalArgumentException("Either owner_pub_key and sender_pub_key_for_add_operation or "
                                           "sender_pub_key_for_add_operation_bytes and owner_pub_key_bytes must be provided.")
        
        self._sender_pub_key_for_add_operation_bytes = sender_pub_key_for_add_operation_bytes
        self._sender_pub_key_for_add_operation = sender_pub_key_for_add_operation
        self._owner_pub_key = owner_pub_key
        self._owner_pub_key_bytes = owner_pub_key_bytes

        self.extra_data_map = None
        if ttl:
            # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
            # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
            # field in a class would break that hash and therefore break the storage mechanism.

            # We add optional TTL entry in v 1.5.5 so we can support different TTL for trade messages and for AckMessages

            # We do not permit longer TTL as the default one
            if ttl < self.TTL:
                self.extra_data_map: Optional[dict[str, str]] = {}
                self.extra_data_map[self.EXTRA_MAP_KEY_TTL] = str(ttl)
            else:
                self.extra_data_map = None

        elif extra_data_map:
            self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(extra_data_map)

    @property
    def sender_pub_key_for_add_operation_bytes(self) -> bytes:
        if self._sender_pub_key_for_add_operation_bytes is None:
            self._sender_pub_key_for_add_operation_bytes = Sig.get_public_key_bytes(self._sender_pub_key_for_add_operation)
        return self._sender_pub_key_for_add_operation_bytes
    
    @property
    def sender_pub_key_for_add_operation(self) -> 'DSA.DsaKey':
        if self._sender_pub_key_for_add_operation is None:
            self._sender_pub_key_for_add_operation = Sig.get_public_key_from_bytes(self._sender_pub_key_for_add_operation_bytes)
        return self._sender_pub_key_for_add_operation

    @property
    def owner_pub_key_bytes(self) -> 'bytes':
        if self._owner_pub_key_bytes is None:
            self._owner_pub_key_bytes = Sig.get_public_key_bytes(self._owner_pub_key)
        return self._owner_pub_key_bytes
    
    @property
    def owner_pub_key(self) -> 'DSA.DsaKey':
        if self._owner_pub_key is None:
            self._owner_pub_key = Sig.get_public_key_from_bytes(self._owner_pub_key_bytes)
        return self._owner_pub_key
    

    # PROTO BUFFER

    def to_proto_message(self) -> protobuf.StoragePayload:
        payload = protobuf.MailboxStoragePayload(
            prefixed_sealed_and_signed_message=self.prefixed_sealed_and_signed_message.to_proto_network_envelope().prefixed_sealed_and_signed_message,
            sender_pub_key_for_add_operation_bytes=self.sender_pub_key_for_add_operation_bytes,
            owner_pub_key_bytes=self.owner_pub_key_bytes
        )
        if self.extra_data_map:
            payload.extra_data.update(self.extra_data_map)
        return payload

    @staticmethod
    def from_proto(proto: protobuf.MailboxStoragePayload) -> 'MailboxStoragePayload':
        return MailboxStoragePayload(
            PrefixedSealedAndSignedMessage.from_payload_proto(proto.prefixed_sealed_and_signed_message),
            sender_pub_key_for_add_operation_bytes=proto.sender_pub_key_for_add_operation_bytes,
            owner_pub_key_bytes=proto.owner_pub_key_bytes,
            extra_data_map=dict(proto.extra_data) if bool(proto.extra_data) else None
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
    
    def get_owner_pub_key(self) -> 'DSA.DsaKey':
        return self.owner_pub_key

    def get_extra_data_map(self) -> Optional[dict[str, str]]:
        return self.extra_data_map
    
    def __eq__(self, other):
        if not isinstance(other, MailboxStoragePayload):
            return False
        return (self.prefixed_sealed_and_signed_message == other.prefixed_sealed_and_signed_message and
                self.sender_pub_key_for_add_operation_bytes == other.sender_pub_key_for_add_operation_bytes and
                self.owner_pub_key_bytes == other.owner_pub_key_bytes and
                self.extra_data_map == other.extra_data_map)

    def __hash__(self):
        return hash(self.serialize_for_hash())
