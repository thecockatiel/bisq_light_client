from typing import TYPE_CHECKING, Optional

from bisq.core.dao.state.model.governance.dao_phase import DaoPhase


if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.cycle import Cycle
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.blockchain.tx import Tx


class PeriodService:

    def __init__(self, dao_state_service: "DaoStateService"):
        self.dao_state_service = dao_state_service

    @property
    def cycles(self) -> list["Cycle"]:
        return self.dao_state_service.cycles

    @property
    def current_cycle(self) -> Optional["Cycle"]:
        return self.dao_state_service.current_cycle

    @property
    def chain_height(self) -> int:
        return self.dao_state_service.chain_height

    def get_optional_tx(self, tx_id: str) -> Optional[Tx]:
        return self.dao_state_service.get_tx(tx_id)

    def get_current_phase(self) -> DaoPhase.Phase:
        current_cycle = self.current_cycle
        if current_cycle:
            return (
                current_cycle.get_phase_for_height(self.chain_height)
                or DaoPhase.Phase.UNDEFINED
            )
        return DaoPhase.Phase.UNDEFINED

    def is_first_block_in_cycle(self, height: int) -> bool:
        cycle = self.get_cycle(height)
        return cycle is not None and cycle.height_of_first_block == height

    def is_last_block_in_cycle(self, height: int) -> bool:
        cycle = self.get_cycle(height)
        return cycle is not None and cycle.height_of_last_block == height

    def get_cycle(self, height: int) -> Optional["Cycle"]:
        return self.dao_state_service.get_cycle(height)

    def is_in_phase(self, height: int, phase: DaoPhase.Phase) -> bool:
        cycle = self.get_cycle(height)
        return cycle is not None and cycle.is_in_phase(height, phase)

    def is_tx_in_phase(self, tx_id: str, phase: DaoPhase.Phase) -> bool:
        tx = self.get_optional_tx(tx_id)
        return tx is not None and self.is_in_phase(tx.block_height, phase)

    def is_tx_in_phase_and_cycle(
        self, tx_id: str, phase: DaoPhase.Phase, current_chain_head_height: int
    ) -> bool:
        return self.is_tx_in_phase(tx_id, phase) and self.is_tx_in_correct_cycle(
            tx_id, current_chain_head_height
        )

    def get_phase_for_height(self, height: int) -> DaoPhase.Phase:
        cycle = self.get_cycle(height)
        phase = cycle.get_phase_for_height(height) if cycle else None
        return phase or DaoPhase.Phase.UNDEFINED

    def is_tx_in_correct_cycle(
        self, tx_height: int, current_chain_head_height: int
    ) -> bool:
        cycle = self.get_cycle(tx_height)
        return (
            cycle is not None
            and cycle.height_of_first_block
            <= current_chain_head_height
            <= cycle.height_of_last_block
        )

    def is_tx_in_correct_cycle_by_id(
        self, tx_id: str, current_chain_head_height: int
    ) -> bool:
        tx = self.get_optional_tx(tx_id)
        return tx is not None and self.is_tx_in_correct_cycle(
            tx.block_height, current_chain_head_height
        )

    def _is_tx_height_in_past_cycle(
        self, tx_height: int, current_chain_head_height: int
    ) -> bool:
        cycle = self.get_cycle(tx_height)
        return (
            cycle is not None and current_chain_head_height > cycle.height_of_last_block
        )

    def get_duration_for_phase(self, phase: DaoPhase.Phase, height: int) -> int:
        cycle = self.get_cycle(height)
        return cycle.get_duration_of_phase(phase) if cycle else 0

    def is_tx_in_past_cycle(self, tx_id: str, chain_height: int) -> bool:
        tx = self.get_optional_tx(tx_id)
        return tx is not None and self._is_tx_height_in_past_cycle(
            tx.block_height, chain_height
        )

    def get_first_block_of_phase(self, height: int, phase: DaoPhase.Phase) -> int:
        cycle = self.get_cycle(height)
        return cycle.get_first_block_of_phase(phase) if cycle else 0

    def is_first_block_in_current_cycle(self) -> bool:
        chain_height = self.chain_height
        return (
            self.get_first_block_of_phase(chain_height, DaoPhase.Phase.PROPOSAL)
            == chain_height
        )

    def get_last_block_of_phase(self, height: int, phase: DaoPhase.Phase) -> int:
        cycle = self.get_cycle(height)
        return cycle.get_last_block_of_phase(phase) if cycle else 0

    def is_in_phase_but_not_last_block(self, phase: DaoPhase.Phase) -> bool:
        chain_height = self.chain_height
        return self.is_in_phase(
            chain_height, phase
        ) and chain_height != self.get_last_block_of_phase(chain_height, phase)
