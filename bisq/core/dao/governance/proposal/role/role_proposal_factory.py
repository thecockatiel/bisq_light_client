from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.proposal.base_proposal_factory import BaseProposalFactory
from bisq.core.dao.state.model.governance.role_proposal import (
    RoleProposal,
)

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.role import Role
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.role.role_validator import (
        RoleValidator,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class RoleProposalFactory(BaseProposalFactory["RoleProposal"]):
    """Creates RoleProposal and transaction."""

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "RoleValidator",
    ):
        super().__init__(
            bsq_wallet_service,
            btc_wallet_service,
            dao_state_service,
            proposal_validator,
        )
        self._role: Optional["Role"] = None

    def create_proposal_with_transaction(self, role: "Role"):
        self._role = role

        return super().create_proposal_with_transaction(role.name, role.link)

    def create_proposal_without_tx_id(
        self,
    ) -> RoleProposal:
        return RoleProposal.from_role(
            self._role,
            {},
        )
