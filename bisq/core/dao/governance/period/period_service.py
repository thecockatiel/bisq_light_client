
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService

# TODO

class PeriodService:
    
    def __init__(self, dao_state_service: "DaoStateService"):
        self.dao_state_service = dao_state_service
    
    def get_chain_height(self) -> int:
        return self.dao_state_service.get_chain_height()