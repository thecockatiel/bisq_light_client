from enum import Enum


class RejectCode(Enum):
    MALFORMED = 0x01
    """The message was not able to be parsed"""
    INVALID = 0x10
    """The message described an invalid object"""
    OBSOLETE = 0x11
    """The message was obsolete or described an object which is obsolete (eg unsupported, old version, v1 block)"""
    DUPLICATE = 0x12
    """
    The message was relayed multiple times or described an object which is in conflict with another.
    This message can describe errors in protocol implementation or the presence of an attempt to DOUBLE SPEND.
    """
    NONSTANDARD = 0x40
    """
    The message described an object was not standard and was thus not accepted.
    Bitcoin Core has a concept of standard transaction forms, which describe scripts and encodings which
    it is willing to relay further. Other transactions are neither relayed nor mined, though they are considered
    valid if they appear in a block.
    """
    DUST = 0x41
    """
    This refers to a specific form of NONSTANDARD transactions, which have an output smaller than some constant
    defining them as dust (this is no longer used).
    """
    INSUFFICIENTFEE = 0x42
    """The messages described an object which did not have sufficient fee to be relayed further."""
    CHECKPOINT = 0x43
    """The message described a block which was invalid according to hard-coded checkpoint blocks."""
    OTHER = 0xFF

    def __init__(self, code: int):
        self.code = code

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    @classmethod
    def from_code(cls, code: int) -> 'RejectCode':
        for reject_code in cls:
            if reject_code.code == code:
                return reject_code
        return cls.OTHER
