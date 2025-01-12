from typing import TYPE_CHECKING
from bisq.core.dao.state.dao_state_listener import DaoStateListener

if TYPE_CHECKING:
    from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.burningman.burning_man_service import BurningManService
    from bisq.core.dao.state.dao_state_service import DaoStateService


# TODO
class BurningManPresentationService(DaoStateListener):
    """Provides APIs for burningman data representation in the UI."""

    def __init__(self, burning_man_service: "BurningManService"):
        self.burning_man_service = burning_man_service
        self.burning_man_candidates_by_name = dict[str, "BurningManCandidate"]()
        self.current_chain_height = 0

    def get_burning_man_candidates_by_name(self) -> dict[str, "BurningManCandidate"]:
        # Cached value is only used for currentChainHeight
        if self.burning_man_candidates_by_name:
            return self.burning_man_candidates_by_name

        self.burning_man_candidates_by_name.update(
            self.burning_man_service.get_burning_man_candidates_by_name(
                self.current_chain_height
            )
        )
        return self.burning_man_candidates_by_name
