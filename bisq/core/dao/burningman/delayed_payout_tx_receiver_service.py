
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.burningman.burning_man_service import BurningManService
    from bisq.core.dao.state.dao_state_service import DaoStateService

# TODO: complete implementation if necessary

class DelayedPayoutTxReceiverService:
    
    def __init__(self, dao_state_service: "DaoStateService", burning_man_service: "BurningManService") -> None:
        self.dao_state_service = dao_state_service
        self.burning_man_service = burning_man_service
        

    def get_burning_man_selection_height(self) -> int:
        return 0