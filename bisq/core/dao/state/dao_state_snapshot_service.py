from collections.abc import Callable
from typing import Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.dao_state_listener import DaoStateListener

logger = get_logger(__name__)


# TODO
class DaoStateSnapshotService(DaoSetupService, DaoStateListener):
    SNAPSHOT_GRID = 20

    def __init__(self):
        self.dao_requires_restart_handler: Optional[Callable[[], None]] = None

    def add_listeners(self):
        pass

    def start(self):
        pass
