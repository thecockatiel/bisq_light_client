from enum import IntEnum

"""
Represents priority used at truncating data set at getDataResponse if total data exceeds limits.
"""
class GetDataResponsePriority(IntEnum):
    LOW = 0
    MID = 1
    HIGH = 2