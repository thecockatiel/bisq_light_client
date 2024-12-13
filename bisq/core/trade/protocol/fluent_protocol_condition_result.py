
from enum import Enum
from typing import Optional


class FluentProtocolConditionResult(Enum):
    VALID = True
    INVALID_PHASE = False
    INVALID_STATE = False
    INVALID_PRE_CONDITION = False
    INVALID_TRADE_ID = False
            
    def __init__(self, is_valid: bool):
        self.is_valid = is_valid
        self.info: Optional[str] = None

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def with_info(self, info: str): # NOTE: even in java enum data is shared between instances
        self.info = info
        return self