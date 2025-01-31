from typing import TYPE_CHECKING, TypeVar
import random

from bisq.common.util.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.support.dispute.agent.dispute_agent_manager import (
        DisputeAgentManager,
    )
    from bisq.core.support.dispute.agent.dispute_agent import DisputeAgent

T = TypeVar("T", bound="DisputeAgent")


class DisputeAgentSelection:
    LOOK_BACK_RANGE = 100

    @staticmethod
    def get_random_mediator(dispute_agent_manager: "DisputeAgentManager[T]") -> T:
        return DisputeAgentSelection.get_random_dispute_agent(dispute_agent_manager)

    @staticmethod
    def get_random_refund_agent(dispute_agent_manager: "DisputeAgentManager[T]") -> T:
        return DisputeAgentSelection.get_random_dispute_agent(dispute_agent_manager)

    @staticmethod
    def get_random_dispute_agent(dispute_agent_manager: "DisputeAgentManager[T]") -> T:
        dispute_agents = list(dispute_agent_manager.observable_map.values())
        random.shuffle(dispute_agents)

        if not dispute_agents:
            check_argument(dispute_agents, "dispute_agents must not be empty")

        return dispute_agents[0]
