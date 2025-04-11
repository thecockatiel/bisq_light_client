from typing import Optional
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.issuance_proposal import IssuanceProposal
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bitcoinj.base.coin import Coin
from bisq.common.protocol.proto_util import ProtoUtil
from utils.time import get_time_ms
import pb_pb2 as protobuf


class ReimbursementProposal(Proposal, IssuanceProposal, ImmutableDaoStateModel):

    def __init__(
        self,
        name: str,
        link: str,
        bsq_address: str,
        requested_bsq: int,
        version: int,
        creation_date: int,
        tx_id: Optional[str],
        extra_data_map: Optional[dict[str, str]] = None,
    ):
        super().__init__(name, link, version, creation_date, tx_id, extra_data_map)
        self.requested_bsq = requested_bsq
        self.bsq_address = bsq_address

    @staticmethod
    def from_coin(
        name: str,
        link: str,
        requested_bsq: Coin,
        bsq_address: str,
        extra_data_map: Optional[dict[str, str]] = None,
    ):
        return ReimbursementProposal(
            name,
            link,
            bsq_address,
            requested_bsq.value,
            Version.REIMBURSEMENT_REQUEST,
            get_time_ms(),
            None,
            extra_data_map,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        reimbursement_proposal = protobuf.ReimbursementProposal(
            requested_bsq=self.requested_bsq,
            bsq_address=self.bsq_address,
        )
        proposal = super().get_proposal_builder()
        proposal.reimbursement_proposal.CopyFrom(reimbursement_proposal)
        return proposal

    @staticmethod
    def from_proto(proto: protobuf.Proposal) -> "ReimbursementProposal":
        proposal_proto = proto.reimbursement_proposal
        return ReimbursementProposal(
            proto.name,
            proto.link,
            proposal_proto.bsq_address,
            proposal_proto.requested_bsq,
            proto.version,
            proto.creation_date,
            proto.tx_id,
            ProtoUtil.to_string_map(proto.extra_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_bsq_address(self):
        return self.bsq_address

    def get_tx_id(self):
        return self.tx_id

    def get_requested_bsq(self) -> Coin:
        return Coin.value_of(self.requested_bsq)

    def get_type(self) -> ProposalType:
        return ProposalType.REIMBURSEMENT_REQUEST

    def get_quorum_param(self) -> Param:
        return Param.QUORUM_REIMBURSEMENT

    def get_threshold_param(self) -> Param:
        return Param.THRESHOLD_REIMBURSEMENT

    def get_tx_type(self) -> str:
        return TxType.REIMBURSEMENT_REQUEST

    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "ReimbursementProposal":
        return ReimbursementProposal(
            self.name,
            self.link,
            self.bsq_address,
            self.requested_bsq,
            self.version,
            self.creation_date,
            tx_id,
            self.extra_data_map,
        )

    def __str__(self) -> str:
        return (
            f"ReimbursementProposal{{\n"
            f"     requestedBsq={self.requested_bsq},\n"
            f"     bsqAddress='{self.bsq_address}',\n"
            f"}} {super().__str__()}"
        )
