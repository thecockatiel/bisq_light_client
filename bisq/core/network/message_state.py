from enum import IntEnum


class MessageState(IntEnum):
    UNDEFINED = 0
    SENT = 1
    ARRIVED = 2
    STORED_IN_MAILBOX = 3
    ACKNOWLEDGED = 4
    FAILED = 5
