from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.proposal.base_proposal_factory import BaseProposalFactory
from bisq.core.dao.state.model.governance.remove_asset_proposal import (
    RemoveAssetProposal,
)

if TYPE_CHECKING:
    from bisq.asset.asset import Asset
    from bisq.core.dao.state.model.governance.remove_asset_proposal import (
        RemoveAssetProposal,
    )
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.remove_asset.remove_asset_validator import (
        RemoveAssetValidator,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class RemoveAssetProposalFactory(BaseProposalFactory["RemoveAssetProposal"]):
    """Creates RemoveAssetProposal and transaction."""

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "RemoveAssetValidator",
    ):
        super().__init__(
            bsq_wallet_service,
            btc_wallet_service,
            dao_state_service,
            proposal_validator,
        )
        self._asset: Optional["Asset"] = None

    def create_proposal_with_transaction(self, name: str, link: str, asset: "Asset"):
        self._asset = asset
        return super().create_proposal_with_transaction(name, link)

    def create_proposal_without_tx_id(
        self,
    ) -> RemoveAssetProposal:
        return RemoveAssetProposal(
            name=self.name,
            link=self.link,
            ticker_symbol=self._asset.get_ticker_symbol(),
            extra_data_map={},
        )
