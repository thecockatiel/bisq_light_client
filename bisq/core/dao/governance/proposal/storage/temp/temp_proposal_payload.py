from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Union
from bisq.common.crypto.sig import Sig, DSA
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
    ProtectedStoragePayload,
)
from bisq.core.dao.state.model.governance.proposal import Proposal
import pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil


class TempProposalPayload(
    ProcessOncePersistableNetworkPayload,
    ProtectedStoragePayload,
    ExpirablePayload,
    PersistablePayload,
):
    """
    TempProposalPayload is wrapper for proposal sent over wire as well as it gets persisted.
    Data size: about 1.245 bytes (pubKey makes it big)
    """

    # We keep data 2 months to be safe if we increase durations of cycle. Also give a bit more resilience in case
    # of any issues with the append-only data store
    TTL_MS = int(timedelta(days=60).total_seconds() * 1000)

    def __init__(
        self,
        proposal: "Proposal",
        owner_pub_key_or_its_bytes: Union[bytes, "DSA.DsaKey"],
        extra_data_map: Optional[dict[str, str]] = None,
    ):
        self.proposal = proposal
        if isinstance(owner_pub_key_or_its_bytes, bytes):
            self._owner_pub_key_encoded = owner_pub_key_or_its_bytes  # bytes
            # Used just for caching. Don't persist.
            self._owner_pub_key = None  # transient
        else:
            self._owner_pub_key_encoded = None
            # Used just for caching. Don't persist.
            self._owner_pub_key = owner_pub_key_or_its_bytes  # transient

        # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
        # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
        # field in a class would break that hash and therefore break the storage mechanism.
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(
            extra_data_map
        )

    @property
    def owner_pub_key_encoded(self):
        if self._owner_pub_key_encoded is None:
            self._owner_pub_key_encoded = Sig.get_public_key_bytes(self._owner_pub_key)
        return self._owner_pub_key_encoded

    @property
    def owner_pub_key(self):
        if self._owner_pub_key is None:
            self._owner_pub_key = Sig.get_public_key_from_bytes(
                self._owner_pub_key_encoded
            )
        return self._owner_pub_key

    def to_proto_message(self):
        return protobuf.StoragePayload(
            temp_proposal_payload=protobuf.TempProposalPayload(
                proposal=self.proposal.to_proto_message(),
                owner_pub_key_encoded=self.owner_pub_key_encoded,
                extra_data=ProtoUtil.to_string_map_entry_list(self.extra_data_map),
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.TempProposalPayload) -> "TempProposalPayload":
        return TempProposalPayload(
            proposal=Proposal.from_proto(proto.proposal),
            owner_pub_key_or_its_bytes=proto.owner_pub_key_encoded,
            extra_data_map=ProtoUtil.to_string_map(proto.extra_data),
        )

    def get_owner_pub_key(self):
        return self.owner_pub_key

    def get_extra_data_map(self):
        return self.extra_data_map

    def get_ttl(self):
        return TempProposalPayload.TTL_MS

    def __eq__(self, value):
        if not isinstance(value, TempProposalPayload):
            return False
        return (
            self.proposal == value.proposal
            and self.owner_pub_key_encoded == value.owner_pub_key_encoded
            and self.extra_data_map == value.extra_data_map
        )

    def __hash__(self):
        return hash(
            (
                self.proposal,
                self.owner_pub_key_encoded,
                tuple(self.extra_data_map.items()) if self.extra_data_map else None,
            )
        )
