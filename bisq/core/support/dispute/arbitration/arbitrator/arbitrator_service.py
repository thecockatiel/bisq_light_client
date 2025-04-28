from typing import TYPE_CHECKING
from bisq.core.support.dispute.agent.dispute_agent_service import DisputeAgentService
from bisq.core.support.dispute.arbitration.arbitrator.arbitrator import Arbitrator

if TYPE_CHECKING:
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService

class ArbitratorService(DisputeAgentService[Arbitrator]):
    
    def __init__(self, p2p_service: "P2PService", filter_manager: "FilterManager"):
        super().__init__(p2p_service, filter_manager)

    def get_dispute_agent_set(self, banned_dispute_agents: list[str]) -> set["Arbitrator"]:
        return {
            data.protected_storage_payload
            for data in self.p2p_service.data_map.values()
            if isinstance(data.protected_storage_payload, Arbitrator)
            and (banned_dispute_agents is None or
                 data.protected_storage_payload.node_address.get_full_address() not in banned_dispute_agents)
        }

    def get_dispute_agents_from_filter(self) -> list[str]:
        return self.filter_manager.get_filter().arbitrators if self.filter_manager.get_filter() else []

    def get_arbitrators(self):
        return self.get_dispute_agents()

