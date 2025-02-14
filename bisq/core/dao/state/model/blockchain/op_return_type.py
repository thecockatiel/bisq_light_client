from enum import Enum
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel


class OpReturnType(ImmutableDaoStateModel, Enum):
    """Provides byte constants for distinguishing the type of a DAO transaction used in the OP_RETURN data."""

    UNDEFINED = 0x00
    PROPOSAL = 0x10
    COMPENSATION_REQUEST = 0x11
    REIMBURSEMENT_REQUEST = 0x12
    BLIND_VOTE = 0x13
    VOTE_REVEAL = 0x14
    LOCKUP = 0x15
    ASSET_LISTING_FEE = 0x16
    PROOF_OF_BURN = 0x17

    def __init__(self, type: int):
        self.type = type

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @staticmethod
    def get_op_return_type(type: int):
        return next(
            (
                op_return_type
                for op_return_type in OpReturnType
                if op_return_type.type == type
            ),
            None,
        )
