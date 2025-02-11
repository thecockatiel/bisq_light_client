from typing import Optional
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.role import Role
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from utils.time import get_time_ms
import pb_pb2 as protobuf


class ConfiscateBondProposal(Proposal, ImmutableDaoStateModel):

    def __init__(
        self,
        name: str,
        link: str,
        lockup_tx_id: str,
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
        self.lockup_tx_id = lockup_tx_id

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        proposal = super().get_proposal_builder()
        proposal.confiscate_bond_proposal.CopyFrom(
            protobuf.ConfiscateBondProposal(
                lockup_tx_id=self.lockup_tx_id,
            )
        )
        return proposal

    @staticmethod
    def from_proto(proto: protobuf.Proposal) -> "ConfiscateBondProposal":
        proposal_proto = proto.confiscate_bond_proposal
        return ConfiscateBondProposal(
            proto.name,
            proto.link,
            proposal_proto.lockup_tx_id,
            proto.version,
            proto.creation_date,
            proto.tx_id,
            dict(proto.extra_data) if proto.extra_data else None,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_type(self) -> ProposalType:
        return ProposalType.CONFISCATE_BOND

    def get_quorum_param(self) -> Param:
        return Param.QUORUM_CONFISCATION

    def get_threshold_param(self) -> Param:
        return Param.THRESHOLD_CONFISCATION

    def get_tx_type(self) -> str:
        return TxType.PROPOSAL

    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "ConfiscateBondProposal":
        return ConfiscateBondProposal(
            self.name,
            self.link,
            self.lockup_tx_id,
            self.version,
            self.creation_date,
            tx_id,
            self.extra_data_map,
        )

    def __str__(self) -> str:
        return (
            f"ConfiscateBondProposal{{\n"
            f"    lockup_tx_id={self.lockup_tx_id},\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, ConfiscateBondProposal):
            return False
        if not super().__eq__(other):
            return False
        return self.lockup_tx_id == other.lockup_tx_id

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.lockup_tx_id))
