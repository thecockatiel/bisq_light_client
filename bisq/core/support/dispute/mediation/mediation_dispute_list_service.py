
from typing import TYPE_CHECKING
from bisq.core.support.dispute.dispute_list_service import DisputeListService
from bisq.core.support.dispute.mediation.mediation_dispute_list import MediationDisputeList

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager

class MediationDisputeListService(DisputeListService[MediationDisputeList]):
    
    def __init__(self, persistence_manager: "PersistenceManager[MediationDisputeList]") :
        super().__init__(persistence_manager)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_concrete_dispute_list(self):
        return MediationDisputeList()
