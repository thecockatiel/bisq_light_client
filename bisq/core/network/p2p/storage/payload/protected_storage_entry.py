from typing import TYPE_CHECKING, Optional

from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.encryption import Encryption
from bisq.common.crypto.hash import get_32_byte_hash
from bisq.common.crypto.sig import Sig, DSA
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.network.p2p.storage.data_and_seq_nr_pair import DataAndSeqNrPair
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import (
    MailboxStoragePayload,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
    ProtectedStoragePayload,
    wrap_in_storage_payload,
)
import pb_pb2 as protobuf
from utils.clock import Clock
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bisq.common.protocol.network.get_data_response_priority import (
        GetDataResponsePriority,
    )
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver



class ProtectedStorageEntry(NetworkPayload, PersistablePayload):

    def __init__(
        self,
        protected_storage_payload: ProtectedStoragePayload,
        sequence_number: int,
        signature: bytes,
        clock: Clock,
        creation_time_stamp: int = None,
        owner_pub_key: Optional["DSA.DsaKey"] = None,
        owner_pub_key_bytes: Optional[bytes] = None,
    ):
        self.logger = get_ctx_logger(__name__)
        if creation_time_stamp is None:
            creation_time_stamp = clock.millis()

        check_argument(
            not isinstance(protected_storage_payload, PersistableNetworkPayload),
            "protected_storage_payload cannot be an instance of PersistableNetworkPayload",
        )

        if owner_pub_key is None and owner_pub_key_bytes is None:
            raise IllegalArgumentException(
                "Either owner_pub_key or owner_public_key_bytes must be provided."
            )

        self.protected_storage_payload = protected_storage_payload
        self._owner_pub_key = owner_pub_key
        self._owner_pub_key_bytes = owner_pub_key_bytes
        self.sequence_number = sequence_number
        self.signature = signature
        # We don't allow creation date in the future, but we cannot be too strict as clocks are not synced
        self.creation_time_stamp = min(creation_time_stamp, clock.millis())

    @property
    def owner_pub_key(self) -> "DSA.DsaKey":
        if self._owner_pub_key is None:
            self._owner_pub_key = Sig.get_public_key_from_bytes(
                self._owner_pub_key_bytes
            )
        return self._owner_pub_key

    @property
    def owner_pub_key_bytes(self) -> bytes:
        if self._owner_pub_key_bytes is None:
            self._owner_pub_key_bytes = Sig.get_public_key_bytes(self._owner_pub_key)
        return self._owner_pub_key_bytes

    # PROTO BUFFER

    def to_proto_message(self):
        return protobuf.ProtectedStorageEntry(
            storage_payload=wrap_in_storage_payload(
                self.protected_storage_payload.to_proto_message()
            ),
            owner_pub_key_bytes=self.owner_pub_key_bytes,
            sequence_number=self.sequence_number,
            signature=self.signature,
            creation_time_stamp=self.creation_time_stamp,
        )

    def to_protected_storage_entry(self) -> "protobuf.ProtectedStorageEntry":
        return self.to_proto_message()

    @staticmethod
    def from_proto(
        proto: "protobuf.ProtectedStorageEntry", resolver: "NetworkProtoResolver"
    ) -> "ProtectedStorageEntry":
        return ProtectedStorageEntry(
            ProtectedStoragePayload.from_proto(proto.storage_payload, resolver),
            proto.sequence_number,
            proto.signature,
            resolver.get_clock(),
            proto.creation_time_stamp,
            owner_pub_key_bytes=proto.owner_pub_key_bytes,
        )

    # API

    def back_date(self):
        if isinstance(self.protected_storage_payload, ExpirablePayload):
            self.creation_time_stamp -= self.protected_storage_payload.get_ttl() // 2

    def is_expired(self, clock: Clock) -> bool:
        return (
            isinstance(self.protected_storage_payload, ExpirablePayload)
            and (clock.millis() - self.creation_time_stamp)
            > self.protected_storage_payload.get_ttl()
        )

    def get_data_response_priority(self) -> "GetDataResponsePriority":
        return self.protected_storage_payload.get_data_response_priority()

    def is_valid_for_add_operation(self) -> bool:
        """
        Returns true if the Entry is valid for an add operation. For non-mailbox Entrys, the entry owner must
        match the payload owner.
        """
        if not self.is_signature_valid():
            return False

        if isinstance(self.protected_storage_payload, MailboxStoragePayload):
            return (
                self.protected_storage_payload.sender_pub_key_for_add_operation_bytes
                == self.owner_pub_key_bytes
            )
        else:
            result = Encryption.is_pubkeys_equal(
                self.owner_pub_key_bytes,
                self.protected_storage_payload.get_owner_pub_key_bytes(),
            )
            if not result:
                res1 = str(self)
                res2 = "null"
                if self.protected_storage_payload.get_owner_pub_key_bytes() != None:
                    res2 = Sig.get_public_key_as_hex_string(
                        self.protected_storage_payload.get_owner_pub_key_bytes(), True
                    )

                self.logger.warning(
                    f"ProtectedStorageEntry::isValidForAddOperation() failed. Entry owner does not match Payload owner:\n"
                    f"ProtectedStorageEntry={res1}\nPayloadOwner={res2}"
                )
            return result

    def is_valid_for_remove_operation(self) -> bool:
        """
        Returns true if the Entry is valid for a remove operation. For non-mailbox Entrys, the entry owner must
        match the payload owner.
        """
        # Same requirements as add()
        result = self.is_valid_for_add_operation()

        if not result:
            res1 = str(self)
            res2 = "null"
            if self.protected_storage_payload.get_owner_pub_key_bytes() != None:
                res2 = Sig.get_public_key_as_hex_string(
                    self.protected_storage_payload.get_owner_pub_key_bytes(), True
                )
            self.logger.warning(
                f"ProtectedStorageEntry::isValidForRemoveOperation() failed. Entry owner does not match Payload owner:\n"
                f"ProtectedStorageEntry={res1}\nPayloadOwner={res2}"
            )
        return result

    def is_signature_valid(self) -> bool:
        """
        Returns true if the signature for the Entry is valid for the payload, sequence number, and ownerPubKey
        """
        try:
            hash_of_data_and_seq_nr = get_32_byte_hash(
                DataAndSeqNrPair(
                    protected_storage_payload=self.protected_storage_payload,
                    sequence_number=self.sequence_number,
                )
            )
            result = Sig.verify(
                self.owner_pub_key, hash_of_data_and_seq_nr, self.signature
            )
            if not result:
                self.logger.warning(
                    f"Invalid signature for {self.protected_storage_payload.__class__.__name__}.\n"
                    f"Serialized data as hex={self.protected_storage_payload.serialize_for_hash().hex()}"
                )
            return result
        except CryptoException as e:
            self.logger.error(
                f"ProtectedStorageEntry::isSignatureValid() exception {str(e)}"
            )
            return False

    def matches_relevant_pub_key(
        self, protected_storage_entry: "ProtectedStorageEntry"
    ) -> bool:
        result = protected_storage_entry.owner_pub_key_bytes == self.owner_pub_key_bytes
        if not result:
            self.logger.warning(
                f"New data entry does not match our stored data. storedData.ownerPubKey={Sig.get_public_key_as_hex_string(protected_storage_entry.owner_pub_key)}\n"
                f"ownerPubKey={Sig.get_public_key_as_hex_string(self.owner_pub_key)}"
            )
        return result

    def __str__(self) -> str:
        return (
            f"ProtectedStorageEntry {{\n\tPayload: {self.protected_storage_payload}\n\t"
            f"Owner Public Key: {Sig.get_public_key_as_hex_string(self.owner_pub_key)}\n\t"
            f"Sequence Number: {self.sequence_number}\n\tSignature: {self.signature.hex()}\n\t"
            f"Timestamp: {self.creation_time_stamp}\n}}"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, ProtectedStorageEntry):
            return False
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(
            (
                self.owner_pub_key_bytes,
                self.sequence_number,
                self.protected_storage_payload,
            )
        )
