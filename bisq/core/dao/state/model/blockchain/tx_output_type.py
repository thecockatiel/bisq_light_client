from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel


class TxOutputType(ImmutableDaoStateModel, IntEnum):
    UNDEFINED = 0  # only fallback for backward compatibility in case we add a new value and old clients fall back to UNDEFINED
    UNDEFINED_OUTPUT = 1
    GENESIS_OUTPUT = 2
    BSQ_OUTPUT = 3
    BTC_OUTPUT = 4
    PROPOSAL_OP_RETURN_OUTPUT = 5
    COMP_REQ_OP_RETURN_OUTPUT = 6
    REIMBURSEMENT_OP_RETURN_OUTPUT = 7
    CONFISCATE_BOND_OP_RETURN_OUTPUT = 8
    ISSUANCE_CANDIDATE_OUTPUT = 9
    BLIND_VOTE_LOCK_STAKE_OUTPUT = 10
    BLIND_VOTE_OP_RETURN_OUTPUT = 11
    VOTE_REVEAL_UNLOCK_STAKE_OUTPUT = 12
    VOTE_REVEAL_OP_RETURN_OUTPUT = 13
    ASSET_LISTING_FEE_OP_RETURN_OUTPUT = 14
    PROOF_OF_BURN_OP_RETURN_OUTPUT = 15
    LOCKUP_OUTPUT = 16
    LOCKUP_OP_RETURN_OUTPUT = 17
    UNLOCK_OUTPUT = 18
    INVALID_OUTPUT = 19

    @staticmethod
    def from_proto(proto: protobuf.TxOutputType) -> "TxOutputType":
        return ProtoUtil.enum_from_proto(TxOutputType, protobuf.TxOutputType, proto)

    def to_proto_message(self):
        return ProtoUtil.proto_enum_from_enum(protobuf.TxOutputType, self)
