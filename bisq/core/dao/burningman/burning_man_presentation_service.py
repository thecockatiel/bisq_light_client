from typing import TYPE_CHECKING
from bisq.common.config.config import Config
from bisq.core.dao.cycles_in_dao_state_service import CyclesInDaoStateService
from bisq.core.dao.governance.proposal.my_proposal_list_service import (
    MyProposalListService,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener

if TYPE_CHECKING:
    from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.burningman.burning_man_service import BurningManService
    from bisq.core.dao.state.dao_state_service import DaoStateService


# TODO
class BurningManPresentationService(DaoStateListener):
    """Provides APIs for burningman data representation in the UI."""

    # Burn target gets increased by that amount to give more flexibility.
    # Burn target is calculated from reimbursements + estimated BTC fees - burned amounts.
    BURN_TARGET_BOOST_AMOUNT = 10000000
    LEGACY_BURNING_MAN_DPT_NAME = "Legacy Burningman (DPT)"
    LEGACY_BURNING_MAN_BTC_FEES_NAME = "Legacy Burningman (BTC fees)"
    LEGACY_BURNING_MAN_BTC_FEES_ADDRESS = "38bZBj5peYS3Husdz7AH3gEUiUbYRD951t"

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        cycles_in_dao_state_service: "CyclesInDaoStateService",
        my_proposal_list_service: "MyProposalListService",
        bsq_wallet_service: "BsqWalletService",
        burning_man_service: "BurningManService",
    ):
        self._dao_state_service = dao_state_service
        self._cycles_in_dao_state_service = cycles_in_dao_state_service
        self._my_proposal_list_service = my_proposal_list_service
        self._bsq_wallet_service = bsq_wallet_service
        self._burning_man_service = burning_man_service
        self.burning_man_candidates_by_name = dict[str, "BurningManCandidate"]()
        self.current_chain_height = 0

    @property
    def genesis_tx_id(self):
        return self._dao_state_service.genesis_tx_id

    def get_burning_man_candidates_by_name(self) -> dict[str, "BurningManCandidate"]:
        # Cached value is only used for currentChainHeight
        if self.burning_man_candidates_by_name:
            return self.burning_man_candidates_by_name

        self.burning_man_candidates_by_name.update(
            self._burning_man_service.get_burning_man_candidates_by_name(
                self.current_chain_height
            )
        )
        return self.burning_man_candidates_by_name
