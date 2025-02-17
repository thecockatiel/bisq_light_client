from typing import TYPE_CHECKING
from bisq.core.dao.governance.proposal.base_proposal_factory import BaseProposalFactory
from bisq.core.dao.state.model.governance.generic_proposal import (
    GenericProposal,
)

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.generic_proposal import GenericProposal
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.generic.generic_proposal_validator import (
        GenericProposalValidator,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class GenericProposalFactory(BaseProposalFactory["GenericProposal"]):
    """Creates GenericProposal and transaction."""

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "GenericProposalValidator",
    ):
        super().__init__(
            bsq_wallet_service,
            btc_wallet_service,
            dao_state_service,
            proposal_validator,
        )

    def create_proposal_with_transaction(self, name: str, link: str):
        return super().create_proposal_with_transaction(name, link)

    def create_proposal_without_tx_id(
        self,
    ) -> GenericProposal:
        return GenericProposal(
            name=self.name,
            link=self.link,
            extra_data_map={},
        )
