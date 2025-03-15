from enum import Enum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel


class TxType(ImmutableDaoStateModel, Enum):
    UNDEFINED = (
        False,
        False,
    )  # only fallback for backward compatibility in case we add a new value and old clients fall back to UNDEFINED
    UNDEFINED_TX_TYPE = (False, False)
    UNVERIFIED = (False, False)
    INVALID = (False, False)
    GENESIS = (False, False)
    TRANSFER_BSQ = (False, False)
    PAY_TRADE_FEE = (False, True)
    PROPOSAL = (True, True)
    COMPENSATION_REQUEST = (True, True)
    REIMBURSEMENT_REQUEST = (True, True)
    BLIND_VOTE = (True, True)
    VOTE_REVEAL = (True, False)
    LOCKUP = (True, False)
    UNLOCK = (True, False)
    ASSET_LISTING_FEE = (True, True)
    PROOF_OF_BURN = (True, True)
    IRREGULAR = (
        False,
        False,
    )  # the params are irrelevant here as we can have any tx that violated the rules set to irregular

    def __init__(self, has_op_return: bool, requires_fee: bool):
        self.has_op_return = has_op_return
        self.requires_fee = requires_fee

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @staticmethod
    def from_proto(proto: protobuf.TxType) -> "TxType":
        return ProtoUtil.enum_from_proto(TxType, protobuf.TxType, proto)

    def to_proto_message(self):
        return ProtoUtil.proto_enum_from_enum(protobuf.TxType, self)

