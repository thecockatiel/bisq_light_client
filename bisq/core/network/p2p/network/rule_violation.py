from enum import Enum

class RuleViolation(Enum):
    INVALID_DATA_TYPE = 2
    WRONG_NETWORK_ID = 0
    MAX_MSG_SIZE_EXCEEDED = 2
    THROTTLE_LIMIT_EXCEEDED = 2
    TOO_MANY_REPORTED_PEERS_SENT = 2
    PEER_BANNED = 0
    INVALID_CLASS = 2

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def __init__(self, max_tolerance: int):
        self.max_tolerance = max_tolerance

    def __str__(self):
        return f"RuleViolation{{max_tolerance={self.max_tolerance}}} {super().__str__()}"
