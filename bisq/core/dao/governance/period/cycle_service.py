from typing import TYPE_CHECKING
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
from bisq.core.dao.state.model.governance.cycle import Cycle

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService


# TODO
class CycleService(DaoStateListener, DaoSetupService):

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        genesis_tx_info: "GenesisTxInfo",
    ):
        self.dao_state_service = dao_state_service
        self.genesis_block_height = genesis_tx_info.genesis_block_height
