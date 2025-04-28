from enum import IntEnum
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class DaoPhase(PersistablePayload, ImmutableDaoStateModel):
    """
    Encapsulated the phase enum with the duration.
    As the duration can change by voting we don't want to put the duration property in the enum but use that wrapper.
    """

    class Phase(ImmutableDaoStateModel, IntEnum):
        """
        Enum for phase of a cycle.

        We don't want to use an enum with the duration as field because the duration can change by voting and enums
        should be considered immutable.
        """

        UNDEFINED = 0
        PROPOSAL = 1
        BREAK1 = 2
        BLIND_VOTE = 3
        BREAK2 = 4
        VOTE_REVEAL = 5
        BREAK3 = 6
        RESULT = 7

    def __init__(self, phase: "DaoPhase.Phase", duration: int):
        self.phase = phase
        self.duration = duration

    def to_proto_message(self) -> "protobuf.DaoPhase":
        return protobuf.DaoPhase(
            phase_ordinal=self.phase.value,
            duration=self.duration,
        )

    @staticmethod
    def from_proto(proto: "protobuf.DaoPhase") -> "DaoPhase":
        ordinal = proto.phase_ordinal
        if ordinal >= len(DaoPhase.Phase):
            logger = get_ctx_logger(__name__)
            logger.warning(
                f"We tried to access an ordinal outside of the DaoPhase.Phase enum bounds and set it to UNDEFINED. ordinal={ordinal}"
            )
            return DaoPhase(DaoPhase.Phase.UNDEFINED, 0)

        return DaoPhase(DaoPhase.Phase(ordinal), proto.duration)

    def __str__(self):
        return (
            f"DaoPhase{{\n"
            f"     phase={self.phase},\n"
            f"     duration={self.duration}\n"
            f"}}"
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, DaoPhase):
            return False
        return self.duration == other.duration and self.phase.name == other.phase.name

    def __hash__(self):
        return hash((self.phase.name, self.duration))
