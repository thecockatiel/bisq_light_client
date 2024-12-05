from enum import IntEnum

from bisq.common.protocol.proto_util import ProtoUtil


class MessageState(IntEnum):
    UNDEFINED = 0
    SENT = 1
    ARRIVED = 2
    STORED_IN_MAILBOX = 3
    ACKNOWLEDGED = 4
    FAILED = 5

    @staticmethod
    def from_string(state: str):
        return ProtoUtil.enum_from_proto(MessageState, state)
