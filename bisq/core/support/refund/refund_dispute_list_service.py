
from typing import TYPE_CHECKING
from bisq.core.support.dispute.dispute_list_service import DisputeListService
from bisq.core.support.refund.refund_dispute_list import RefundDisputeList

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager

class RefundDisputeListService(DisputeListService[RefundDisputeList]):
    
    def __init__(self, persistence_manager: "PersistenceManager[RefundDisputeList]") :
        super().__init__(persistence_manager)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_concrete_dispute_list(self):
        return RefundDisputeList()
