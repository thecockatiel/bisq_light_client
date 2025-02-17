from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.proofofburn.my_proof_of_burn_list import MyProofOfBurnList

if TYPE_CHECKING:
    from bisq.core.dao.governance.proofofburn.my_proof_of_burn import MyProofOfBurn
    from bisq.common.persistence.persistence_manager import PersistenceManager


class MyProofOfBurnListService(PersistedDataHost, DaoSetupService):
    """Manages the persistence of MyProofOfBurn objects."""

    def __init__(self, persistence_manager: "PersistenceManager[MyProofOfBurnList]"):
        self._persistence_manager = persistence_manager
        self._my_proof_of_burn_list = MyProofOfBurnList()
        self._persistence_manager.initialize(
            self._my_proof_of_burn_list, PersistenceManagerSource.PRIVATE
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def on_persisted(persisted: "MyProofOfBurnList") -> None:
            self._my_proof_of_burn_list.set_all(persisted.list)
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

    def add_my_proof_of_burn(self, my_proof_of_burn: "MyProofOfBurn") -> None:
        if my_proof_of_burn not in self._my_proof_of_burn_list:
            self._my_proof_of_burn_list.append(my_proof_of_burn)
            self._request_persistence()

    def get_my_proof_of_burn_list(self):
        return self._my_proof_of_burn_list.list

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _request_persistence(self) -> None:
        self._persistence_manager.request_persistence()
