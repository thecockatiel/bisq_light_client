from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class IssuanceType(ImmutableDaoStateModel, IntEnum):
    UNDEFINED = 0
    COMPENSATION = 1
    REIMBURSEMENT = 2

    @staticmethod
    def from_name(name: str) -> "IssuanceType":
        try:
            return IssuanceType[name]
        except:
            return IssuanceType.UNDEFINED
