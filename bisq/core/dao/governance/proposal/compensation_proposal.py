from typing import Optional
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.issuance_proposal import IssuanceProposal
from bisq.core.dao.governance.proposal.proposal import Proposal
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bitcoinj.base.coin import Coin
from utils.time import get_time_ms
import pb_pb2 as protobuf


class CompensationProposal(Proposal, IssuanceProposal, ImmutableDaoStateModel):
    # Keys for extra map
    BURNING_MAN_RECEIVER_ADDRESS = "burningManReceiverAddress"

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
        return CompensationProposal(
            name,
            link,
            bsq_address,
            requested_bsq.value,
            Version.COMPENSATION_REQUEST,
            get_time_ms(),
            None,
            extra_data_map,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        compensation_proposal = protobuf.CompensationProposal(
            requested_bsq=self.requested_bsq,
            bsq_address=self.bsq_address,
        )
        proposal = super().get_proposal_builder()
        proposal.compensation_proposal.CopyFrom(compensation_proposal)
        return proposal

    @staticmethod
    def from_proto(proto: protobuf.Proposal) -> "CompensationProposal":
        proposal_proto = proto.compensation_proposal
        return CompensationProposal(
            proto.name,
            proto.link,
            proposal_proto.bsq_address,
            proposal_proto.requested_bsq,
            proto.version,
            proto.creation_date,
            proto.tx_id,
            dict(proto.extra_data) if proto.extra_data else None,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_requested_bsq(self) -> Coin:
        return Coin.value_of(self.requested_bsq)

    def get_type(self) -> ProposalType:
        return ProposalType.COMPENSATION_REQUEST

    def get_quorum_param(self) -> Param:
        return Param.QUORUM_COMP_REQUEST

    def get_threshold_param(self) -> Param:
        return Param.THRESHOLD_COMP_REQUEST

    def get_tx_type(self) -> str:
        return TxType.COMPENSATION_REQUEST

    # Added at v.1.9.7
    def get_burning_man_receiver_address(self) -> Optional[str]:
        if self.extra_data_map:
            return self.extra_data_map.get(
                CompensationProposal.BURNING_MAN_RECEIVER_ADDRESS
            )
        return None

    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "CompensationProposal":
        return CompensationProposal(
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
            f"CompensationProposal{{\n"
            f"     requestedBsq={self.requested_bsq},\n"
            f"     bsqAddress='{self.bsq_address}',\n"
            f"     burningManReceiverAddress='{self.get_burning_man_receiver_address()}'\n"
            f"}} {super().__str__()}"
        )
