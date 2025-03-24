from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
import pb_pb2 as protobuf
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from utils.pb_helper import map_to_stable_extra_data

if TYPE_CHECKING:
    from bisq.core.dao.governance.param.param import Param


class Proposal(
    PersistablePayload, NetworkPayload, ConsensusCritical, ImmutableDaoStateModel, ABC
):
    """Base class for proposals."""

    def __init__(
        self,
        name: str,
        link: str,
        version: int,
        creation_date: int,
        tx_id: Optional[str] = None,
        extra_data_map: Optional[dict[str, str]] = None,
    ):
        self.name = name
        self.link = link
        self.version = version
        self.creation_date = creation_date
        self.tx_id = tx_id
        # This hash map allows addition of data in future versions without breaking consensus
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(
            extra_data_map
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        builder = protobuf.Proposal(
            name=self.name,
            link=self.link,
            version=self.version,
            creation_date=self.creation_date,
        )
        if self.extra_data_map:
            builder.extra_data.extend(map_to_stable_extra_data(self.extra_data_map))
        if self.tx_id:
            builder.tx_id = self.tx_id
        return builder

    def to_proto_message(self):
        return self.get_proposal_builder()

    @staticmethod
    def from_proto(proto: protobuf.Proposal):
        if proto.HasField("compensation_proposal"):
            from bisq.core.dao.state.model.governance.compensation_proposal import (
                CompensationProposal,
            )

            return CompensationProposal.from_proto(proto)
        elif proto.HasField("reimbursement_proposal"):
            from bisq.core.dao.state.model.governance.reimbursement_proposal import (
                ReimbursementProposal,
            )

            return ReimbursementProposal.from_proto(proto)
        elif proto.HasField("change_param_proposal"):
            from bisq.core.dao.state.model.governance.change_param_proposal import (
                ChangeParamProposal,
            )

            return ChangeParamProposal.from_proto(proto)
        elif proto.HasField("role_proposal"):
            from bisq.core.dao.state.model.governance.role_proposal import RoleProposal

            return RoleProposal.from_proto(proto)
        elif proto.HasField("confiscate_bond_proposal"):
            from bisq.core.dao.state.model.governance.confiscate_bond_proposal import (
                ConfiscateBondProposal,
            )

            return ConfiscateBondProposal.from_proto(proto)
        elif proto.HasField("generic_proposal"):
            from bisq.core.dao.state.model.governance.generic_proposal import (
                GenericProposal,
            )

            return GenericProposal.from_proto(proto)
        elif proto.HasField("remove_asset_proposal"):
            from bisq.core.dao.state.model.governance.remove_asset_proposal import (
                RemoveAssetProposal,
            )

            return RemoveAssetProposal.from_proto(proto)
        else:
            raise ProtobufferException(f"Unknown message case: {proto}")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_creation_date_as_date(self) -> datetime:
        return datetime.fromtimestamp(self.creation_date / 1000)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "Proposal":
        pass

    @abstractmethod
    def get_type(self) -> "ProposalType":
        pass

    @abstractmethod
    def get_tx_type(self) -> "TxType":
        pass

    @abstractmethod
    def get_quorum_param(self) -> "Param":
        pass

    @abstractmethod
    def get_threshold_param(self) -> "Param":
        pass

    def __str__(self) -> str:
        return (
            f"Proposal{{\n"
            f"     txId='{self.tx_id}',\n"
            f"     name='{self.name}',\n"
            f"     link='{self.link}',\n"
            f"     extraDataMap={self.extra_data_map},\n"
            f"     version={self.version},\n"
            f"     creationDate={self.get_creation_date_as_date()}\n"
            f"}}"
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Proposal):
            return False
        return (
            self.version == other.version
            and self.creation_date == other.creation_date
            and self.name == other.name
            and self.link == other.link
            and self.tx_id == other.tx_id
            and self.extra_data_map == other.extra_data_map
        )

    def __hash__(self):
        return hash(
            (
                self.version,
                self.creation_date,
                self.name,
                self.link,
                self.tx_id,
                tuple(self.extra_data_map.items()) if self.extra_data_map else None,
            )
        )
