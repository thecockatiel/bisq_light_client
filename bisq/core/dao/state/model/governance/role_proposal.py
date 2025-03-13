from typing import Optional
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.role import Role
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from utils.pb_helper import stable_extra_data_to_map
from utils.time import get_time_ms
import pb_pb2 as protobuf


class RoleProposal(Proposal, ImmutableDaoStateModel):

    def __init__(
        self,
        name: str,
        link: str,
        role: Role,
        required_bond_unit: int,
        unlock_time: int,
        version: int = None,
        creation_date: int = None,
        tx_id: Optional[str] = None,
        extra_data_map: Optional[dict[str, str]] = None,
    ):
        if version is None:
            version = Version.PROPOSAL
        if creation_date is None:
            creation_date = get_time_ms()
        super().__init__(name, link, version, creation_date, tx_id, extra_data_map)
        self.role = role
        self.required_bond_unit = required_bond_unit
        self.unlock_time = unlock_time  # in blocks

    @staticmethod
    def from_role(
        role: Role,
        extra_data_map: Optional[dict[str, str]] = None,
    ) -> "RoleProposal":
        return RoleProposal(
            role.name,
            role.link,
            role,
            role.bonded_role_type.required_bond_unit,
            role.bonded_role_type.unlock_time_in_blocks,
            extra_data_map=extra_data_map,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        proposal = super().get_proposal_builder()
        proposal.role_proposal.CopyFrom(
            protobuf.RoleProposal(
                role=self.role.to_proto_message(),
                required_bond_unit=self.required_bond_unit,
                unlock_time=self.unlock_time,
            )
        )
        return proposal

    @staticmethod
    def from_proto(proto: protobuf.Proposal) -> "RoleProposal":
        proposal_proto = proto.role_proposal
        return RoleProposal(
            proto.name,
            proto.link,
            Role.from_proto(proposal_proto.role),
            proposal_proto.required_bond_unit,
            proposal_proto.unlock_time,
            proto.version,
            proto.creation_date,
            proto.tx_id,
            stable_extra_data_to_map(proto.extra_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_type(self) -> ProposalType:
        return ProposalType.BONDED_ROLE

    def get_quorum_param(self) -> Param:
        return Param.QUORUM_ROLE

    def get_threshold_param(self) -> Param:
        return Param.THRESHOLD_ROLE

    def get_tx_type(self) -> str:
        return TxType.PROPOSAL

    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "RoleProposal":
        return RoleProposal(
            self.name,
            self.link,
            self.role,
            self.required_bond_unit,
            self.unlock_time,
            self.version,
            self.creation_date,
            tx_id,
            self.extra_data_map,
        )

    def __str__(self) -> str:
        return (
            f"RoleProposal{{\n"
            f"     role={self.role},\n"
            f"     requiredBondUnit={self.required_bond_unit},\n"
            f"     unlockTime={self.unlock_time},\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, RoleProposal):
            return False
        if not super().__eq__(other):
            return False
        return (
            self.role == other.role
            and self.required_bond_unit == other.required_bond_unit
            and self.unlock_time == other.unlock_time,
        )

    def __hash__(self) -> int:
        return hash(
            (
                super().__hash__(),
                self.role,
                self.required_bond_unit,
                self.unlock_time,
            )
        )
