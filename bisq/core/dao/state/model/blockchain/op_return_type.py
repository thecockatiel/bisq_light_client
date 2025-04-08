from enum import Enum
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel


class OpReturnType(ImmutableDaoStateModel, Enum):
    """Provides byte constants for distinguishing the type of a DAO transaction used in the OP_RETURN data."""

    UNDEFINED = b"\x00"
    PROPOSAL = b"\x10"
    COMPENSATION_REQUEST = b"\x11"
    REIMBURSEMENT_REQUEST = b"\x12"
    BLIND_VOTE = b"\x13"
    VOTE_REVEAL = b"\x14"
    LOCKUP = b"\x15"
    ASSET_LISTING_FEE = b"\x16"
    PROOF_OF_BURN = b"\x17"

    def __init__(self, type: bytes):
        self.type = type

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @staticmethod
    def get_op_return_type(type: bytes):
        return next(
            (
                op_return_type
                for op_return_type in OpReturnType
                if op_return_type.type == type
            ),
            None,
        )
