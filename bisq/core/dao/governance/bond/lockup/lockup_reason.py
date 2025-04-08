from enum import Enum


class LockupReason(Enum):
    """Reason for locking up a bond."""

    UNDEFINED = b"\x00"
    BONDED_ROLE = b"\x01"
    REPUTATION = b"\x02"

    def __init__(self, id: bytes):
        self.id = id

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @staticmethod
    def get_lockup_reason(id: bytes):
        return next((reason for reason in LockupReason if reason.id == id), None)
