from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.sig import Sig
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
    ProtectedStoragePayload,
)
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal


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
        owner_pub_key_encoded: bytes,
        extra_data_map: Optional[dict[str, str]] = None,
    ):
        self.proposal = proposal
        self.owner_pub_key_encoded = owner_pub_key_encoded

        # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
        # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
        # field in a class would break that hash and therefore break the storage mechanism.
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(
            extra_data_map
        )

        #  Used just for caching. Don't persist.
        self.owner_pub_key = Sig.get_public_key_from_bytes(
            owner_pub_key_encoded
        )  # transient

    def to_proto_message(self):
        return protobuf.StoragePayload(
            temp_proposal_payload=protobuf.TempProposalPayload(
                proposal=self.proposal.to_proto_message(),
                owner_pub_key_encoded=self.owner_pub_key_encoded,
                extra_data=self.extra_data_map,
            )
        )

    @classmethod
    def from_proto(proto: protobuf.TempProposalPayload) -> "TempProposalPayload":
        return TempProposalPayload(
            proposal=Proposal.from_proto(proto.proposal),
            owner_pub_key_encoded=proto.owner_pub_key_encoded,
            extra_data_map=dict(proto.extra_data) if proto.extra_data else None,
        )

    def get_owner_pub_key(self):
        return self.owner_pub_key

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
                tuple(self.extra_data_map.items()),
            )
        )
