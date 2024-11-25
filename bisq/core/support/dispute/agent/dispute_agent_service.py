from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Set, TypeVar, Generic, Callable
from bisq.common.app.dev_env import DevEnv
from bisq.common.config.config import CONFIG
from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.hash_map_changed_listener import HashMapChangedListener
    from bisq.core.support.dispute.agent.dispute_agent import DisputeAgent
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.common.handlers.result_handler import ResultHandler
    from bisq.core.network.p2p.node_address import NodeAddress

T = TypeVar('T', bound='DisputeAgent')

logger = get_logger(__name__)

class DisputeAgentService(ABC, Generic[T]):
    def __init__(self, p2p_service: "P2PService", filter_manager: "FilterManager"):
        self.p2p_service = p2p_service
        self.filter_manager = filter_manager

    @abstractmethod
    def get_dispute_agent_set(self, banned_dispute_agents: List[str]) -> Set[T]:
        pass

    @abstractmethod
    def get_dispute_agents_from_filter(self) -> List[str]:
        pass
    
    def add_hash_set_changed_listener(self, hash_map_changed_listener: "HashMapChangedListener"):
        self.p2p_service.add_hash_set_changed_listener(hash_map_changed_listener)

    def add_dispute_agent(self, dispute_agent: T,
                         result_handler: "ResultHandler",
                         error_message_handler: "ErrorMessageHandler") -> None:
        logger.debug(f"addDisputeAgent hash(dispute_agent) {hash(dispute_agent)}")
        if not CONFIG.base_currency_network.is_mainnet() or \
                dispute_agent.registration_pub_key.hex() != DevEnv.DEV_PRIVILEGE_PUB_KEY:
            result = self.p2p_service.add_protected_storage_entry(dispute_agent)
            if result:
                logger.trace(f"Add disputeAgent to network was successful. hash(dispute_agent) = {hash(dispute_agent)}")
                result_handler()
            else:
                error_message_handler("Add disputeAgent failed")
        else:
            logger.error("Attempt to publish dev disputeAgent on mainnet.")
            error_message_handler("Add disputeAgent failed. Attempt to publish dev disputeAgent on mainnet.")

    def remove_dispute_agent(self, dispute_agent: T,
                            result_handler: "ResultHandler",
                            error_message_handler: "ErrorMessageHandler") -> None:
        logger.debug(f"removeDisputeAgent hash(dispute_agent) {hash(dispute_agent)}")
        if self.p2p_service.remove_data(dispute_agent):
            logger.trace(f"Remove disputeAgent from network was successful. hash(dispute_agent) = {hash(dispute_agent)}")
            result_handler()
        else:
            error_message_handler("Remove disputeAgent failed")

    def get_dispute_agents(self) -> Dict["NodeAddress", T]:
        banned_dispute_agents: Optional[List[str]] = None
        
        if self.filter_manager.get_filter() is not None:
            banned_dispute_agents = self.get_dispute_agents_from_filter()

        if banned_dispute_agents is not None and banned_dispute_agents:
            logger.warning(f"banned_dispute_agents={banned_dispute_agents}")

        dispute_agent_set = self.get_dispute_agent_set(banned_dispute_agents)

        dispute_map: Dict["NodeAddress", T] = {}
        for dispute_agent in dispute_agent_set:
            dispute_agent_node_address = dispute_agent.node_address
            if dispute_agent_node_address not in dispute_map:
                dispute_map[dispute_agent_node_address] = dispute_agent
            else:
                logger.warning("dispute_agent_address already exists in dispute_agent map. "
                             "Seems a dispute_agent object is already registered with the same address.")
        
        return dispute_map