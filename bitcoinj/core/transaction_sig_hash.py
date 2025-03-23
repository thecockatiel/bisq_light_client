from enum import Enum


class TransactionSigHash(Enum):
    ALL = 1
    NONE = 2
    SINGLE = 3
    ANYONECANPAY = 0x80  # Caution: Using this type in isolation is non-standard. Treated similar to ANYONECANPAY_ALL.
    ANYONECANPAY_ALL = 0x81
    ANYONECANPAY_NONE = 0x82
    ANYONECANPAY_SINGLE = 0x83
    UNSET = 0  # Caution: Using this type in isolation is non-standard. Treated similar to ALL.
    
    def __init__(self, int_value: int):
        self.int_value = int_value

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def byte_value(self) -> int:
        return self.int_value
