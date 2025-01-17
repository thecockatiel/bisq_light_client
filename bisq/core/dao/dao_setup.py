from collections.abc import Callable
from bisq.core.dao.dao_setup_service import DaoSetupService


# TODO
class DaoSetup:
    """
    High level entry point for Dao domain.
    We initialize all main service classes here to be sure they are started.
    """

    def __init__(self):
        self.dao_setup_services: list["DaoSetupService"] = []

    def on_all_services_initialized(
        self,
        error_message_handler: Callable[[str], None],
        warn_message_handler: Callable[[str], None],
    ):
        pass

    def shut_down(self):
        pass
