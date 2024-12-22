from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.governance.period.cycle_service import CycleService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.cycle import Cycle


# TODO
class CyclesInDaoStateService:
    """
    Utility methods for Cycle related methods.
    As they might be called often we use caching.
    """

    def __init__(
        self, dao_state_service: "DaoStateService", cycle_service: "CycleService"
    ):
        self.dao_state_service = dao_state_service
        self.cycle_service = cycle_service
