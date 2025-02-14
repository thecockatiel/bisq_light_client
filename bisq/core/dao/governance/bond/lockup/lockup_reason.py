from enum import Enum


class LockupReason(Enum):
    """Reason for locking up a bond."""

    UNDEFINED = 0x00
    BONDED_ROLE = 0x01
    REPUTATION = 0x02

    def __init__(self, id: int):
        self.id = id

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @staticmethod
    def get_lockup_reason(id: int):
        return next((reason for reason in LockupReason if reason.id == id), None)
