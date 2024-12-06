
from enum import IntEnum
from bisq.common.protocol.proto_util import ProtoUtil
import proto.pb_pb2 as protobuf

class MediationResultState(IntEnum):
    UNDEFINED_MEDIATION_RESULT = 0
    MEDIATION_RESULT_ACCEPTED = 1
    MEDIATION_RESULT_REJECTED = 2
    SIG_MSG_SENT = 3
    SIG_MSG_ARRIVED = 4
    SIG_MSG_IN_MAILBOX = 5
    SIG_MSG_SEND_FAILED = 6
    RECEIVED_SIG_MSG = 7
    PAYOUT_TX_PUBLISHED = 8
    PAYOUT_TX_PUBLISHED_MSG_SENT = 9
    PAYOUT_TX_PUBLISHED_MSG_ARRIVED = 10
    PAYOUT_TX_PUBLISHED_MSG_IN_MAILBOX = 11
    PAYOUT_TX_PUBLISHED_MSG_SEND_FAILED = 12
    RECEIVED_PAYOUT_TX_PUBLISHED_MSG = 13
    PAYOUT_TX_SEEN_IN_NETWOR = 14
    
    @staticmethod
    def from_proto(proto: protobuf.MediationResultState) -> 'MediationResultState':
        return ProtoUtil.enum_from_proto(MediationResultState, protobuf.MediationResultState, proto)
    
    @staticmethod
    def to_proto_message(state: "MediationResultState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.MediationResultState, state)
