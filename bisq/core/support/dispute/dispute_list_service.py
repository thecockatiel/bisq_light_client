from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, Generic, Set, List, Optional
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.user_thread import UserThread
from utils.data import ObservableChangeEvent, SimpleProperty

if TYPE_CHECKING:
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.support.dispute.dispute_list import DisputeList
    from bisq.core.trade.model.bisq_v1.contract import Contract
    from bisq.common.persistence.persistence_manager import PersistenceManager

T = TypeVar('T', bound='DisputeList[Dispute]')

class DisputeListService(Generic[T], PersistedDataHost, ABC):
    def __init__(self, persistence_manager: "PersistenceManager[T]"):
        self._persistence_manager = persistence_manager
        self._dispute_list: T = self.get_concrete_dispute_list()
        self._num_open_disputes = SimpleProperty(0)
        self._disputed_trade_ids: Set[str] = set()
        
        self._persistence_manager.initialize(self._dispute_list, PersistenceManagerSource.PRIVATE, self.get_file_name())

    @property
    def persistence_manager(self) -> "PersistenceManager[T]":
        return self._persistence_manager

    @property
    def dispute_list(self) -> T:
        return self._dispute_list

    @property
    def num_open_disputes(self) -> SimpleProperty[int]:
        return self._num_open_disputes

    @property
    def disputed_trade_ids(self) -> Set[str]:
        return self._disputed_trade_ids
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def get_concrete_dispute_list(self) -> T:
        pass
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def on_persisted(persisted: T) -> None:
            self._dispute_list.set_all(persisted.list)
            complete_handler()
        
        self._persistence_manager.read_persisted(on_persisted, complete_handler, file_name=self.get_file_name())

    def get_file_name(self) -> str:
        return self._dispute_list.get_default_storage_file_name()
    
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Public
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def cleanup_disputes(self, closed_dispute_handler: Optional[Callable[[str], None]] = None) -> None:
        for dispute in self._dispute_list:
            trade_id = dispute.trade_id
            if dispute.is_result_proposed and closed_dispute_handler:
                closed_dispute_handler(trade_id)
                
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // (JAVA) Package scope
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self) -> None:
        self._dispute_list.add_listener(self._on_disputes_change_listener)
        self._on_disputes_change_listener(ObservableChangeEvent(self._dispute_list.list))

    def get_nr_of_disputes(self, is_buyer: bool, contract: "Contract") -> str:
        def filter_dispute(dispute: "Dispute") -> bool:
            contract1 = dispute.contract
            if not contract1:
                return False
            
            if is_buyer:
                buyer_node_address = contract1.buyer_node_address
                return buyer_node_address and buyer_node_address == contract.buyer_node_address
            else:
                seller_node_address = contract1.seller_node_address
                return seller_node_address and seller_node_address == contract.seller_node_address

        return str(len(set(filter(filter_dispute, self.get_observable_list()))))

    def get_observable_list(self) -> List["Dispute"]:
        return self._dispute_list.get_observable_list()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def _on_disputes_change_listener(self, e: ObservableChangeEvent["Dispute"]) -> None:
        if e.removed_elements:
            for dispute in e.removed_elements:
                self._disputed_trade_ids.remove(dispute.trade_id)

        for dispute in e.added_elements:
            # for each dispute added, keep track of its "BadgeCountProperty"
            def on_badge_count_change(is_alerting: int):
                def update_alerts():
                    num_alerts = sum(x.badge_count_property.value for x in self._dispute_list.list)
                    self._num_open_disputes.value = num_alerts
                
                UserThread.execute(update_alerts)

            dispute.badge_count_property.add_listener(on_badge_count_change)
            self._disputed_trade_ids.add(dispute.trade_id)

    def request_persistence(self) -> None:
        self._persistence_manager.request_persistence()

