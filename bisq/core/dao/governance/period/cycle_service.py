from typing import TYPE_CHECKING, Optional
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.governance.cycle import Cycle

if TYPE_CHECKING:
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.dao.state.dao_state_service import DaoStateService


class CycleService(DaoStateListener, DaoSetupService):

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        genesis_tx_info: "GenesisTxInfo",
    ):
        self.dao_state_service = dao_state_service
        self.genesis_block_height = genesis_tx_info.genesis_block_height

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self.dao_state_service.add_dao_state_listener(self)

    def start(self):
        self.add_first_cycle()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_new_block_height(self, block_height: int):
        maybe_new_cycle = self._maybe_create_new_cycle(
            block_height, self.dao_state_service.cycles
        )
        if maybe_new_cycle:
            self.dao_state_service.add_cycle(maybe_new_cycle)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_first_cycle(self):
        self.dao_state_service.add_cycle(self._get_first_cycle())

    def get_cycle_index(self, cycle: "Cycle") -> int:
        try:
            return self.dao_state_service.cycles.index(cycle)
        except:
            return -1

    def is_tx_in_cycle(self, cycle: "Cycle", tx_id: str) -> bool:
        tx = self.dao_state_service.get_tx(tx_id)
        return tx is not None and self._is_block_height_in_cycle(tx.block_height, cycle)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _is_block_height_in_cycle(self, block_height: int, cycle: "Cycle") -> bool:
        return cycle.height_of_first_block <= block_height <= cycle.height_of_last_block

    def _maybe_create_new_cycle(
        self, block_height: int, cycles: list["Cycle"]
    ) -> Optional["Cycle"]:
        # We want to set the correct phase and cycle before we start parsing a new block.
        # For Genesis block we did it already in the start method.
        # We copy over the phases from the current block as we get the phase only set in
        # applyParamToPhasesInCycle if there was a changeEvent.
        # The isFirstBlockInCycle methods returns from the previous cycle the first block as we have not
        # applied the new cycle yet. But the first block of the old cycle will always be the same as the
        # first block of the new cycle.
        if (
            block_height > self.genesis_block_height
            and cycles
            and self._is_first_block_after_previous_cycle(block_height, cycles)
        ):
            # We have the not update dao_state_service.current_cycle so we grab here the previousCycle
            previous_cycle = cycles[-1]
            # We create the new cycle as clone of the previous cycle and only if there have been change events we use
            # the new values from the change event.
            return self._create_new_cycle(block_height, previous_cycle)
        return None

    def _get_first_cycle(self) -> "Cycle":
        # We want to have the initial data set up before the genesis tx gets parsed so we do it here in the constructor
        # as onAllServicesInitialized might get called after the parser has started.
        # We add the default values from the Param enum to our StateChangeEvent list.
        dao_phases_with_default_duration = tuple(
            self._get_phase_with_default_duration(phase) for phase in DaoPhase.Phase
        )
        return Cycle(self.genesis_block_height, dao_phases_with_default_duration)

    def _create_new_cycle(self, block_height: int, previous_cycle: "Cycle") -> "Cycle":
        dao_phase_list = []
        for dao_phase in previous_cycle.dao_phase_list:
            phase = dao_phase.phase
            try:
                param = Param[f"PHASE_{phase.name}"]
                value = self.dao_state_service.get_param_value_as_block(
                    param, block_height
                )
                dao_phase_list.append(DaoPhase(phase, value))
            except:
                continue

        return Cycle(block_height, tuple(dao_phase_list))

    def _is_first_block_after_previous_cycle(
        self, height: int, cycles: list["Cycle"]
    ) -> bool:
        previous_block_height = height - 1
        previous_cycle = self._get_cycle(previous_block_height, cycles)
        return previous_cycle and previous_cycle.height_of_last_block + 1 == height

    def _get_phase_with_default_duration(self, phase: "DaoPhase.Phase") -> "DaoPhase":
        # We will always have a default value defined
        param = next(
            param for param in Param if self._is_param_matching_phase(param, phase)
        )
        return DaoPhase(phase, int(param.default_value))

    def _is_param_matching_phase(self, param: "Param", phase: "DaoPhase.Phase") -> bool:
        return (
            param.name.startswith("PHASE_")
            and param.name.replace("PHASE_", "") == phase.name
        )

    def _get_cycle(self, height: int, cycles: list["Cycle"]) -> Optional["Cycle"]:
        return next(
            (
                cycle
                for cycle in cycles
                if cycle.height_of_first_block <= height <= cycle.height_of_last_block
            ),
            None,
        )
