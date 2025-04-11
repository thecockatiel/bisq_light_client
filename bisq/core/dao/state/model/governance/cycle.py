from typing import Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class Cycle(PersistablePayload, ImmutableDaoStateModel):
    """
    Cycle represents the monthly period for proposals and voting.
    It consists of a ordered list of phases represented by the phaseWrappers.
    """

    def __init__(self, height_of_first_block: int, dao_phase_list: tuple["DaoPhase"]):
        # List is ordered according to the Phase enum.
        self.dao_phase_list = dao_phase_list
        self.height_of_first_block = height_of_first_block

    def to_proto_message(self):
        return protobuf.Cycle(
            height_of_first_block=self.height_of_first_block,
            dao_phase=[
                dao_phase.to_proto_message() for dao_phase in self.dao_phase_list
            ],
        )

    @staticmethod
    def from_proto(proto: protobuf.Cycle) -> "Cycle":
        dao_phase_list = tuple(DaoPhase.from_proto(phase) for phase in proto.dao_phase)
        return Cycle(proto.height_of_first_block, dao_phase_list)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def height_of_last_block(self) -> int:
        return self.height_of_first_block + self.get_duration() - 1

    def is_in_phase(self, height: int, phase: "DaoPhase.Phase") -> bool:
        first_block_of_phase = self.get_first_block_of_phase(phase)
        last_block_of_phase = self.get_last_block_of_phase(phase)
        return first_block_of_phase <= height <= last_block_of_phase

    def is_in_cycle(self, height: int) -> bool:
        return self.height_of_first_block <= height <= self.height_of_last_block

    def get_first_block_of_phase(self, phase: "DaoPhase.Phase") -> int:
        return self.height_of_first_block + sum(
            item.duration
            for item in self.dao_phase_list
            if item.phase.value < phase.value
        )

    def get_last_block_of_phase(self, phase: "DaoPhase.Phase") -> int:
        return self.get_first_block_of_phase(phase) + self.get_duration(phase) - 1

    def get_duration_of_phase(self, phase: "DaoPhase.Phase") -> int:
        return sum(item.duration for item in self.dao_phase_list if item.phase == phase)

    def get_phase_for_height(self, height: int) -> Optional["DaoPhase.Phase"]:
        return next(
            (
                dao_phase.phase
                for dao_phase in self.dao_phase_list
                if self.is_in_phase(height, dao_phase.phase)
            ),
            None,
        )

    def _get_phase_wrapper(self, phase: "DaoPhase.Phase") -> "DaoPhase":
        return next(
            (
                dao_phase
                for dao_phase in self.dao_phase_list
                if dao_phase.phase == phase
            ),
            None,
        )

    def get_duration(self, phase: "DaoPhase.Phase" = None) -> int:
        if phase is None:
            return sum(phase.duration for phase in self.dao_phase_list)
        else:
            phase_wrapper = self._get_phase_wrapper(phase)
            if phase_wrapper is not None:
                return phase_wrapper.duration
            else:
                return 0

    def __str__(self):
        return (
            f"Cycle{{\n"
            f"    dao_phase_list={self.dao_phase_list},\n"
            f"    height_of_first_block={self.height_of_first_block}\n"
            f"}}"
        )
