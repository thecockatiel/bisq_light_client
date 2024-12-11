
from typing import TYPE_CHECKING
from bisq.core.support.dispute.arbitration.arbitration_dispute_list import ArbitrationDisputeList
from bisq.core.support.dispute.dispute_list_service import DisputeListService

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager

class ArbitrationDisputeListService(DisputeListService[ArbitrationDisputeList]):
    
    def __init__(self, persistence_manager: "PersistenceManager[ArbitrationDisputeList]") :
        super().__init__(persistence_manager)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_concrete_dispute_list(self):
        return ArbitrationDisputeList()
    
    def get_file_name(self):
        return "DisputeList"