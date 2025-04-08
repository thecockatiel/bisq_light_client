from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from bisq.common.crypto.sig import Sig, DSA
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import (
    MailboxStoragePayload,
)
from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
    ProtectedStorageEntry,
)
from bisq.common.setup.log_setup import get_logger
from utils.clock import Clock
import pb_pb2 as protobuf
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver

logger = get_logger(__name__)


@dataclass
class ProtectedMailboxStorageEntry(ProtectedStorageEntry):

    def __init__(
        self,
        mailbox_storage_payload: MailboxStoragePayload,
        sequence_number: int,
        signature: bytes,
        clock: Clock,
        creation_time_stamp: int = None,
        owner_pub_key: "DSA.DsaKey" = None,
        owner_pub_key_bytes: bytes = None,
        receivers_pub_key: "DSA.DsaKey" = None,
        receivers_pub_key_bytes: bytes = None,
    ):
        super().__init__(
            mailbox_storage_payload,
            sequence_number,
            signature,
            clock,
            creation_time_stamp=(
                clock.millis() if creation_time_stamp is None else creation_time_stamp
            ),
            owner_pub_key=owner_pub_key,
            owner_pub_key_bytes=owner_pub_key_bytes,
        )
        self._receivers_pub_key = receivers_pub_key
        self._receivers_pub_key_bytes = receivers_pub_key_bytes

    @property
    def receivers_pub_key(self) -> "DSA.DsaKey":
        if self._receivers_pub_key is None:
            self._receivers_pub_key = Sig.get_public_key_from_bytes(
                self._receivers_pub_key_bytes
            )
        return self._receivers_pub_key

    @property
    def receivers_pub_key_bytes(self) -> bytes:
        if self._receivers_pub_key_bytes is None:
            self._receivers_pub_key_bytes = Sig.get_public_key_bytes(
                self._receivers_pub_key
            )
        return self._receivers_pub_key_bytes

    # /////////////////////////////////////////////////////////////////////////////////////////
    # API
    # /////////////////////////////////////////////////////////////////////////////////////////

    @property
    def mailbox_storage_payload(self) -> MailboxStoragePayload:
        check_argument(isinstance(self.protected_storage_payload, MailboxStoragePayload))
        return self.protected_storage_payload

    def is_valid_for_add_operation(self) -> bool:
        """
        Returns true if this Entry is valid for an add operation. For mailbox Entrys, the entry owner must
        match the valid sender Public Key specified in the payload. (Only sender can add)
        """
        if not self.is_signature_valid():
            return False

        mailbox_storage_payload = self.mailbox_storage_payload

        # Verify the Entry.receiversPubKey matches the Payload.ownerPubKey. This is a requirement for removal
        if mailbox_storage_payload.owner_pub_key_bytes != self.receivers_pub_key_bytes:
            logger.debug(
                "Entry receiversPubKey does not match payload owner which is a requirement for adding MailboxStoragePayloads"
            )
            return False

        result = (
            mailbox_storage_payload.sender_pub_key_for_add_operation_bytes
            == self.owner_pub_key_bytes
        )

        if not result:
            res1 = str(self)
            res2 = "null"
            if mailbox_storage_payload.owner_pub_key:
                if mailbox_storage_payload.sender_pub_key_for_add_operation:
                    res2 = Sig.get_public_key_as_hex_string(
                        mailbox_storage_payload.sender_pub_key_for_add_operation, True
                    )

            logger.warning(
                "ProtectedMailboxStorageEntry::isValidForAddOperation() failed. "
                + f"Entry owner does not match sender key in payload:\nProtectedStorageEntry={res1}\n"
                + f"SenderPubKeyForAddOperation={res2}"
            )
        return result

    def is_valid_for_remove_operation(self) -> bool:
        """
        Returns true if the Entry is valid for a remove operation. For mailbox Entrys, the entry owner must
        match the payload owner. (Only receiver can remove)
        """
        if not self.is_signature_valid():
            return False

        mailbox_storage_payload = self.mailbox_storage_payload

        # Verify the Entry has the correct receiversPubKey for removal
        if mailbox_storage_payload.owner_pub_key_bytes != self.receivers_pub_key_bytes:
            logger.debug(
                "Entry receiversPubKey does not match payload owner which is a requirement for removing MailboxStoragePayloads"
            )
            return False

        result = (
            mailbox_storage_payload.owner_pub_key_bytes
            and mailbox_storage_payload.owner_pub_key_bytes == self.owner_pub_key_bytes
        )

        if not result:
            res1 = str(self)
            res2 = "null"
            if mailbox_storage_payload.owner_pub_key_bytes:
                res2 = Sig.get_public_key_as_hex_string(
                    mailbox_storage_payload.owner_pub_key, True
                )

            logger.warning(
                "ProtectedMailboxStorageEntry::isValidForRemoveOperation() failed. "
                + f"Entry owner does not match Payload owner:\nProtectedStorageEntry={res1}\n"
                + f"PayloadOwner={res2}"
            )
        return result

    def matches_relevant_pub_key(
        self, protected_storage_entry: ProtectedStorageEntry
    ) -> bool:
        """
        Returns true if the Entry metadata that is expected to stay constant between different versions of the same object
        matches. For ProtectedMailboxStorageEntry, the receiversPubKey must stay the same.
        """
        if not isinstance(protected_storage_entry, ProtectedMailboxStorageEntry):
            logger.error(
                "ProtectedMailboxStorageEntry::isMetadataEquals() failed due to object type mismatch. "
                + "ProtectedMailboxStorageEntry required, but got\n"
                + str(protected_storage_entry)
            )
            return False

        protected_mailbox_storage_entry = cast(
            ProtectedMailboxStorageEntry, protected_storage_entry
        )

        result = (
            protected_mailbox_storage_entry.receivers_pub_key_bytes
            == self.receivers_pub_key_bytes
        )
        if not result:
            logger.warning(
                "ProtectedMailboxStorageEntry::isMetadataEquals() failed due to metadata mismatch. "
                + f"new.receiversPubKey={Sig.get_public_key_as_hex_string(protected_mailbox_storage_entry.receivers_pub_key_bytes, True)}\n"
                f"stored.receiversPubKey={Sig.get_public_key_as_hex_string(self.receivers_pub_key_bytes, True)}"
            )
        return result

    # /////////////////////////////////////////////////////////////////////////////////////////
    # PROTO BUFFER
    # /////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.ProtectedMailboxStorageEntry:
        return protobuf.ProtectedMailboxStorageEntry(
            entry=super().to_proto_message(),
            receivers_pub_key_bytes=self.receivers_pub_key_bytes,
        )

    @staticmethod
    def from_proto(
        proto: protobuf.ProtectedMailboxStorageEntry, resolver: "NetworkProtoResolver"
    ) -> "ProtectedMailboxStorageEntry":
        entry = ProtectedStorageEntry.from_proto(proto.entry, resolver)
        return ProtectedMailboxStorageEntry(
            entry.protected_storage_payload,
            entry.sequence_number,
            entry.signature,
            resolver.get_clock(),
            entry.creation_time_stamp,
            owner_pub_key_bytes=entry.owner_pub_key_bytes,
            receivers_pub_key_bytes=proto.receivers_pub_key_bytes,
        )

    def __str__(self) -> str:
        return f"ProtectedMailboxStorageEntry:\n\t  Receivers Public Key: {Sig.get_public_key_as_hex_string(self.receivers_pub_key_bytes, True)}\n{super().__str__()}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, ProtectedMailboxStorageEntry):
            return False
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(
            (
                self.owner_pub_key_bytes,
                self.receivers_pub_key_bytes,
                self.sequence_number,
                self.protected_storage_payload,
            )
        )
