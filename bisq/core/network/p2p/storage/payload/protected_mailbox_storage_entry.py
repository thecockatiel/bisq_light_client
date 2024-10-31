from typing import TYPE_CHECKING, cast
from bisq.core.common.crypto.sig import Sig, dsa
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import MailboxStoragePayload
from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
from bisq.logging import get_logger
from utils.clock import Clock
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver

logger = get_logger(__name__)

class ProtectedMailboxStorageEntry(ProtectedStorageEntry):
    def __init__(self,
                 mailbox_storage_payload: MailboxStoragePayload,
                 owner_pub_key: dsa.DSAPublicKey,
                 sequence_number: int,
                 signature: bytes,
                 receivers_pub_key: dsa.DSAPublicKey,
                 clock: Clock,
                 creation_time_stamp: int = None):
        self.receivers_pub_key = receivers_pub_key
        self.receivers_pub_key_bytes = Sig.get_public_key_bytes(receivers_pub_key)
        super().__init__(mailbox_storage_payload,
                         Sig.get_public_key_bytes(owner_pub_key),
                         owner_pub_key,
                         sequence_number,
                         signature,
                         clock,
                         creation_time_stamp= clock.millis() if creation_time_stamp is None else creation_time_stamp)

    #/////////////////////////////////////////////////////////////////////////////////////////
    # API
    #/////////////////////////////////////////////////////////////////////////////////////////

    def get_mailbox_storage_payload(self) -> MailboxStoragePayload:
        return cast(MailboxStoragePayload, super().protected_storage_payload)

    def is_valid_for_add_operation(self) -> bool:
        """
        Returns true if this Entry is valid for an add operation. For mailbox Entrys, the entry owner must
        match the valid sender Public Key specified in the payload. (Only sender can add)
        """
        if not self.is_signature_valid():
            return False

        mailbox_storage_payload = self.get_mailbox_storage_payload()

        # Verify the Entry.receiversPubKey matches the Payload.ownerPubKey. This is a requirement for removal
        if mailbox_storage_payload.get_owner_pub_key() != self.receivers_pub_key:
            logger.debug("Entry receiversPubKey does not match payload owner which is a requirement for adding MailboxStoragePayloads")
            return False

        result = mailbox_storage_payload.sender_pub_key_for_add_operation == self.owner_pub_key

        if not result:
            res1 = str(self)
            res2 = "null"
            if mailbox_storage_payload.get_owner_pub_key():
                if mailbox_storage_payload.sender_pub_key_for_add_operation:
                    res2 = Sig.get_public_key_bytes_as_hex_string(mailbox_storage_payload.sender_pub_key_for_add_operation, True)

            logger.warning("ProtectedMailboxStorageEntry::isValidForAddOperation() failed. " +
                    "Entry owner does not match sender key in payload:\nProtectedStorageEntry=%s\n" +
                    "SenderPubKeyForAddOperation=%s", res1, res2)
        return result

    def is_valid_for_remove_operation(self) -> bool:
        """
        Returns true if the Entry is valid for a remove operation. For mailbox Entrys, the entry owner must
        match the payload owner. (Only receiver can remove)
        """
        if not self.is_signature_valid():
            return False

        mailbox_storage_payload = self.get_mailbox_storage_payload()

        # Verify the Entry has the correct receiversPubKey for removal
        if mailbox_storage_payload.get_owner_pub_key() != self.receivers_pub_key:
            logger.debug("Entry receiversPubKey does not match payload owner which is a requirement for removing MailboxStoragePayloads")
            return False

        result = mailbox_storage_payload.get_owner_pub_key() and mailbox_storage_payload.get_owner_pub_key() == self.owner_pub_key

        if not result:
            res1 = str(self)
            res2 = "null"
            if mailbox_storage_payload.get_owner_pub_key():
                res2 = Sig.get_public_key_bytes_as_hex_string(mailbox_storage_payload.get_owner_pub_key(), True)

            logger.warning("ProtectedMailboxStorageEntry::isValidForRemoveOperation() failed. " +
                    "Entry owner does not match Payload owner:\nProtectedStorageEntry=%s\n" +
                    "PayloadOwner=%s", res1, res2)
        return result

    def matches_relevant_pub_key(self, protected_storage_entry: ProtectedStorageEntry) -> bool:
        """ 
        Returns true if the Entry metadata that is expected to stay constant between different versions of the same object
        matches. For ProtectedMailboxStorageEntry, the receiversPubKey must stay the same.
        """
        if not isinstance(protected_storage_entry, ProtectedMailboxStorageEntry):
            logger.error("ProtectedMailboxStorageEntry::isMetadataEquals() failed due to object type mismatch. " +
                    "ProtectedMailboxStorageEntry required, but got\n" + str(protected_storage_entry))
            return False

        protected_mailbox_storage_entry = cast(ProtectedMailboxStorageEntry, protected_storage_entry)

        result = protected_mailbox_storage_entry.receivers_pub_key == self.receivers_pub_key
        if not result:
            logger.warning("ProtectedMailboxStorageEntry::isMetadataEquals() failed due to metadata mismatch. " +
                    "new.receiversPubKey=%s\nstored.receiversPubKey=%s", 
                    Sig.get_public_key_bytes_as_hex_string(protected_mailbox_storage_entry.receivers_pub_key_bytes, True),
                    Sig.get_public_key_bytes_as_hex_string(self.receivers_pub_key_bytes, True))
        return result

    #/////////////////////////////////////////////////////////////////////////////////////////
    # PROTO BUFFER
    #/////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.ProtectedMailboxStorageEntry:
        return protobuf.ProtectedMailboxStorageEntry(entry=super().to_proto_message(),
                                                     receivers_pub_key_bytes=self.receivers_pub_key_bytes)

    @classmethod
    def from_proto(cls, proto: protobuf.ProtectedMailboxStorageEntry,
                  resolver: 'NetworkProtoResolver') -> 'ProtectedMailboxStorageEntry':
        entry = ProtectedStorageEntry.from_proto(proto.entry, resolver)
        return cls(
            cast(MailboxStoragePayload, entry.protected_storage_payload),
            entry.owner_pub_key,
            entry.sequence_number,
            entry.signature,
            Sig.get_public_key_from_bytes(proto.receivers_pub_key_bytes),
            resolver.get_clock(),
            creation_time_stamp=entry.creation_time_stamp)

    def __str__(self) -> str:
        return f"ProtectedMailboxStorageEntry:\n\t  Receivers Public Key: {Sig.get_public_key_bytes_as_hex_string(self.receivers_pub_key_bytes, True)}\n{super().__str__()}"
