from typing import TYPE_CHECKING

from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bisq.core.dao.governance.period.cycle_service import CycleService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.cycle import Cycle


class CyclesInDaoStateService:
    """
    Utility methods for Cycle related methods.
    As they might be called often we use caching.
    """

    def __init__(
        self, dao_state_service: "DaoStateService", cycle_service: "CycleService"
    ):
        self._dao_state_service = dao_state_service
        self._cycle_service = cycle_service

        # cached result
        self._cycles_by_height: dict[int, "Cycle"] = {}
        self._index_by_cycle: dict["Cycle", int] = {}
        self._cycles_by_index: dict[int, "Cycle"] = {}

    def get_cycle_index_at_chain_height(self, chain_height: int) -> int:
        cycle = self.find_cycle_at_height(chain_height)
        if cycle:
            return self._cycle_service.get_cycle_index(cycle)
        raise IllegalStateException(f"No cycle found for chain height {chain_height}.")

    def get_chain_height_of_past_cycle(
        self, chain_height: int, num_past_cycles: int
    ) -> int:
        """
        Args:
            chain_height (int): Chain height from where we start
            num_past_cycles (int): Number of past cycles
        Returns:
            int: The height at the same offset from the first block of the cycle as in the current cycle minus the past cycles.
        """
        first_block_of_past_cycle = self.get_height_of_first_block_of_past_cycle(
            chain_height, num_past_cycles
        )
        if (
            first_block_of_past_cycle
            == self._dao_state_service.genesis_block_height
        ):
            return first_block_of_past_cycle
        return first_block_of_past_cycle + self.get_offset_from_first_block_in_cycle(
            chain_height
        )

    def get_offset_from_first_block_in_cycle(self, chain_height: int) -> int:
        cycle = self._dao_state_service.get_cycle(chain_height)
        if cycle:
            return chain_height - cycle.height_of_first_block
        return 0

    def get_height_of_first_block_of_past_cycle(
        self, chain_height: int, num_past_cycles: int
    ) -> int:
        cycle = self.find_cycle_at_height(chain_height)
        if cycle:
            target_index = self.get_index_for_cycle(cycle) - num_past_cycles
            # NOTE: setting to same comparison as in java to not cause DAO mismatch
            if target_index > 0:
                return self.get_cycle_at_index(target_index).height_of_first_block
        return self._dao_state_service.genesis_block_height

    def get_cycle_at_index(self, index: int) -> "Cycle":
        check_argument(index >= 0, "Index must be >= 0")
        if index in self._cycles_by_index:
            return self._cycles_by_index[index]
        cycle = self._dao_state_service.get_cycle_at_index(index)
        self._cycles_by_index[index] = cycle
        return cycle

    def get_index_for_cycle(self, cycle: "Cycle") -> int:
        if cycle in self._index_by_cycle:
            return self._index_by_cycle[cycle]
        index = self._cycle_service.get_cycle_index(cycle)
        self._index_by_cycle[cycle] = index
        return index

    def find_cycle_at_height(self, chain_height: int) -> "Cycle":
        if chain_height in self._cycles_by_height:
            return self._cycles_by_height[chain_height]
        cycle = self._dao_state_service.get_cycle(chain_height)
        if cycle:
            self._cycles_by_height[chain_height] = cycle
        return cycle
