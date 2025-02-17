from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.proposal.base_proposal_factory import BaseProposalFactory
from bisq.core.dao.state.model.governance.change_param_proposal import (
    ChangeParamProposal,
)

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.param.change_param_validator import (
        ChangeParamValidator,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class ChangeParamProposalFactory(BaseProposalFactory["ChangeParamProposal"]):
    """Creates ChangeParamProposal and transaction."""

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "ChangeParamValidator",
    ):
        super().__init__(
            bsq_wallet_service,
            btc_wallet_service,
            dao_state_service,
            proposal_validator,
        )
        self._param: Optional[Param] = None
        self._param_value: Optional[str] = None

    def create_proposal_with_transaction(
        self,
        name: str,
        link: str,
        param: Param,
        param_value: str,
    ):
        self._param = param
        self._param_value = param_value

        return super().create_proposal_with_transaction(name, link)

    def create_proposal_without_tx_id(
        self,
    ) -> ChangeParamProposal:
        return ChangeParamProposal(
            name=self.name,
            link=self.link,
            param=self._param,
            param_value=self._param_value,
            extra_data_map={},
        )

