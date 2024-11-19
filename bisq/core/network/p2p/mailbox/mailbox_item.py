from typing import TYPE_CHECKING, Optional

import proto.pb_pb2 as protobuf

from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.network.p2p.decrypted_message_with_pub_key import (
    DecryptedMessageWithPubKey,
)
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import (
    ProtectedMailboxStorageEntry,
)

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from utils.clock import Clock


class MailboxItem(PersistablePayload):
    def __init__(
        self,
        protected_mailbox_storage_entry: ProtectedMailboxStorageEntry,
        decrypted_message_with_pub_key: Optional[DecryptedMessageWithPubKey] = None,
    ):
        self.protected_mailbox_storage_entry = protected_mailbox_storage_entry
        self.decrypted_message_with_pub_key = decrypted_message_with_pub_key

    def to_proto_message(self) -> protobuf.MailboxItem:
        message = protobuf.MailboxItem(
            protected_mailbox_storage_entry=self.protected_mailbox_storage_entry.to_proto_message()
        )

        if self.decrypted_message_with_pub_key:
            message.decrypted_message_with_pub_key.CopyFrom(
                self.decrypted_message_with_pub_key.to_proto_message()
            )

        return message

    @staticmethod
    def from_proto(
        proto: protobuf.MailboxItem,
        network_proto_resolver: "NetworkProtoResolver",
    ) -> "MailboxItem":
        decrypted_message_with_pub_key = (
            DecryptedMessageWithPubKey.from_proto(
                proto.decrypted_message_with_pub_key,
                network_proto_resolver,
            )
            if proto.decrypted_message_with_pub_key
            else None
        )

        return MailboxItem(
            ProtectedMailboxStorageEntry.from_proto(
                proto.protected_mailbox_storage_entry,
                network_proto_resolver,
            ),
            decrypted_message_with_pub_key,
        )

    def is_mine(self) -> bool:
        return self.decrypted_message_with_pub_key is not None

    def get_uid(self) -> str:
        if self.decrypted_message_with_pub_key:
            # We use uid from mailboxMessage in case its ours as we have the at removeMailboxMsg only the
            # decryptedMessageWithPubKey available which contains the mailboxMessage.
            mailbox_message = self.decrypted_message_with_pub_key.network_envelope
            assert isinstance(mailbox_message, MailboxMessage)
            return mailbox_message.uid
        else:
            # If its not our mailbox msg we take the uid from the prefixedSealedAndSignedMessage instead.
            # Those will never be removed via removeMailboxMsg but we clean up expired entries at startup.
            return (
                self.protected_mailbox_storage_entry.get_mailbox_storage_payload().prefixed_sealed_and_signed_message.uid
            )

    def is_expired(self, clock: "Clock") -> bool:
        return self.protected_mailbox_storage_entry.is_expired(clock)
