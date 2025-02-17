from typing import TYPE_CHECKING, Optional
from bisq.common.version import Version
from bisq.core.dao.governance.proposal.base_proposal_factory import BaseProposalFactory
from bisq.core.dao.governance.proposal.proposal_consensus import ProposalConsensus
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from bisq.core.dao.state.model.governance.compensation_proposal import (
    CompensationProposal,
)
from bisq.core.dao.state.model.governance.proposal import Proposal
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction import Transaction


if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.compensation.compensation_validator import (
        CompensationValidator,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class CompensationProposalFactory(BaseProposalFactory["CompensationProposal"]):
    """Creates the CompensationProposal and the transaction."""

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "CompensationValidator",
    ):
        super().__init__(
            bsq_wallet_service,
            btc_wallet_service,
            dao_state_service,
            proposal_validator,
        )
        self._requested_bsq: Optional[Coin] = None
        self._bsq_address: Optional[str] = None
        self._burning_man_receiver_address: Optional[str] = None

    def create_proposal_with_transaction(
        self,
        name: str,
        link: str,
        requested_bsq: Coin,
        burning_man_receiver_address: Optional[str],
    ):
        self._requested_bsq = requested_bsq
        self._burning_man_receiver_address = burning_man_receiver_address
        self._bsq_address = self._bsq_wallet_service.get_unused_bsq_address_as_string()

        return super().create_proposal_with_transaction(name, link)

    def create_proposal_without_tx_id(
        self,
    ) -> CompensationProposal:
        extra_data_map = None
        if self._burning_man_receiver_address:
            extra_data_map = {
                CompensationProposal.BURNING_MAN_RECEIVER_ADDRESS: self._burning_man_receiver_address
            }
        return CompensationProposal(
            name=self.name,
            link=self.link,
            requested_bsq=self._requested_bsq,
            bsq_address=self._bsq_address,
            extra_data_map=extra_data_map,
        )

    def get_op_return_data(self, hash_of_payload: bytes) -> bytes:
        return ProposalConsensus.get_op_return_data(
            hash_of_payload,
            OpReturnType.COMPENSATION_REQUEST.type,
            Version.COMPENSATION_REQUEST,
        )

    def complete_tx(
        self,
        prepared_burn_fee_tx: Transaction,
        op_return_data: bytes,
        proposal: Proposal,
    ) -> Transaction:
        if not isinstance(proposal, CompensationProposal):
            raise IllegalStateException(
                f"Expected CompensationProposal, got {type(proposal).__class__.__name__}"
            )
        return self._btc_wallet_service.complete_prepared_compensation_request_tx(
            proposal.get_requested_bsq(),
            proposal.get_address(),
            prepared_burn_fee_tx,
            op_return_data,
        )
