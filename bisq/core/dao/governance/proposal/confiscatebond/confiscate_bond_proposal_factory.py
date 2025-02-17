from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.base_proposal_factory import BaseProposalFactory
from bisq.core.dao.state.model.governance.confiscate_bond_proposal import (
    ConfiscateBondProposal,
)

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.confiscatebond.confiscate_bond_validator import (
        ConfiscateBondValidator,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class ConfiscateBondProposalFactory(BaseProposalFactory["ConfiscateBondProposal"]):
    """Creates ConfiscateBondProposal and transaction."""

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "ConfiscateBondValidator",
    ):
        super().__init__(
            bsq_wallet_service,
            btc_wallet_service,
            dao_state_service,
            proposal_validator,
        )
        self._lockup_tx_id: Optional[str] = None

    def create_proposal_with_transaction(
        self,
        name: str,
        link: str,
        lockup_tx_id: str,
    ):
        self._lockup_tx_id = lockup_tx_id

        return super().create_proposal_with_transaction(name, link)

    def create_proposal_without_tx_id(
        self,
    ) -> ConfiscateBondProposal:
        return ConfiscateBondProposal(
            name=self.name,
            link=self.link,
            lockup_tx_id=self._lockup_tx_id,
            extra_data_map={},
        )
