from typing import Optional
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from utils.time import get_time_ms
import pb_pb2 as protobuf


class ChangeParamProposal(Proposal, ImmutableDaoStateModel):

    def __init__(
        self,
        name: str,
        link: str,
        param: Param,
        param_value: str,
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
        self.param = param
        self.param_value = param_value

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        change_param_proposal = protobuf.ChangeParamProposal(
            param=self.param.name,
            param_value=self.param_value,
        )
        proposal = super().get_proposal_builder()
        proposal.change_param_proposal.CopyFrom(change_param_proposal)
        return proposal

    @staticmethod
    def from_proto(proto: protobuf.Proposal) -> "ChangeParamProposal":
        proposal_proto = proto.change_param_proposal
        return ChangeParamProposal(
            proto.name,
            proto.link,
            Param.from_proto(proposal_proto.param),
            proposal_proto.param_value,
            proto.version,
            proto.creation_date,
            proto.tx_id,
            dict(proto.extra_data) if proto.extra_data else None,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_type(self) -> ProposalType:
        return ProposalType.CHANGE_PARAM

    def get_quorum_param(self) -> Param:
        return Param.QUORUM_CHANGE_PARAM

    def get_threshold_param(self) -> Param:
        return Param.THRESHOLD_CHANGE_PARAM

    def get_tx_type(self) -> str:
        return TxType.PROPOSAL

    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "ChangeParamProposal":
        return ChangeParamProposal(
            self.name,
            self.link,
            self.param,
            self.param_value,
            self.version,
            self.creation_date,
            tx_id,
            self.extra_data_map,
        )

    def __str__(self) -> str:
        return (
            f"ChangeParamProposal{{"
            f"\n     param={self.param},"
            f"\n     param_value={self.param_value}"
            f"\n}} {super().__str__()}"
        )

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, ChangeParamProposal):
            return False
        if not super().__eq__(other):
            return False
        return (
            self.param.param_type.name == other.param.param_type.name
            and self.param.name == other.param.name
            and self.param_value == other.param_value
        )

    def __hash__(self) -> int:
        return hash(
            (
                super().__hash__(),
                self.param.param_type.name,
                self.param.name,
                self.param_value,
            )
        )
