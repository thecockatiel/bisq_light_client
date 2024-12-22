from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
from proto.pb_pb2 import DaoPhase


# TODO
class Cycle(PersistablePayload, ImmutableDaoStateModel):

    def __init__(self, height_of_first_block: int, dao_phase_list: tuple["DaoPhase"]):
        self.height_of_first_block = height_of_first_block
        self.dao_phase_list = dao_phase_list
