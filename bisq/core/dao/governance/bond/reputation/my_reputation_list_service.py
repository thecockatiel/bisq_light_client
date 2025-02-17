from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.bond.reputation.my_reputation_list import MyReputationList

if TYPE_CHECKING:
    from bisq.core.dao.governance.bond.reputation.my_reputation import MyReputation
    from bisq.common.persistence.persistence_manager import PersistenceManager


class MyReputationListService(PersistedDataHost, DaoSetupService):
    """Manages the persistence of myReputation objects."""

    def __init__(
        self, persistence_manager: "PersistenceManager[MyReputationList]"
    ) -> None:
        self._persistence_manager = persistence_manager
        self._my_reputation_list = MyReputationList()
        self._persistence_manager.initialize(
            self._my_reputation_list, PersistenceManagerSource.PRIVATE
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def on_persisted(persisted: "MyReputationList") -> None:
            self._my_reputation_list.set_all(persisted.list)
            complete_handler()

        self._persistence_manager.read_persisted(on_persisted, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self) -> None:
        pass

    def start(self) -> None:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_reputation(self, reputation: "MyReputation") -> None:
        if reputation not in self._my_reputation_list:
            self._my_reputation_list.append(reputation)
            self._request_persistence()

    @property
    def my_reputation_list(self) -> list["MyReputation"]:
        return self._my_reputation_list.list

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _request_persistence(self) -> None:
        self._persistence_manager.request_persistence()
