from typing import Optional
from bisq.common.version import Version
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.dao.governance.proposal.proposal_type import ProposalType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from bisq.common.protocol.proto_util import ProtoUtil
from utils.time import get_time_ms
import pb_pb2 as protobuf


class RemoveAssetProposal(Proposal, ImmutableDaoStateModel):

    def __init__(
        self,
        name: str,
        link: str,
        ticker_symbol: str,
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
        self.ticker_symbol = ticker_symbol

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proposal_builder(self) -> protobuf.Proposal:
        proposal = super().get_proposal_builder()
        proposal.remove_asset_proposal.CopyFrom(
            protobuf.RemoveAssetProposal(
                ticker_symbol=self.ticker_symbol,
            )
        )
        return proposal

    @staticmethod
    def from_proto(proto: protobuf.Proposal) -> "RemoveAssetProposal":
        proposal_proto = proto.remove_asset_proposal
        return RemoveAssetProposal(
            proto.name,
            proto.link,
            proposal_proto.ticker_symbol,
            proto.version,
            proto.creation_date,
            proto.tx_id,
            ProtoUtil.to_string_map(proto.extra_data),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_type(self) -> ProposalType:
        return ProposalType.REMOVE_ASSET

    def get_quorum_param(self) -> Param:
        return Param.QUORUM_REMOVE_ASSET

    def get_threshold_param(self) -> Param:
        return Param.THRESHOLD_REMOVE_ASSET

    def get_tx_type(self) -> str:
        return TxType.PROPOSAL

    def clone_proposal_and_add_tx_id(self, tx_id: str) -> "RemoveAssetProposal":
        return RemoveAssetProposal(
            self.name,
            self.link,
            self.ticker_symbol,
            self.version,
            self.creation_date,
            tx_id,
            self.extra_data_map,
        )

    def __str__(self) -> str:
        return (
            f"RemoveAssetProposal{{\n"
            f"    ticker_symbol={self.ticker_symbol},\n"
            f"}} {super().__str__()}"
        )

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, RemoveAssetProposal):
            return False
        if not super().__eq__(other):
            return False
        return self.ticker_symbol == other.ticker_symbol

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.ticker_symbol))
