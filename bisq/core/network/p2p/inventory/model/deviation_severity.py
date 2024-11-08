from enum import IntEnum

class DeviationSeverity(IntEnum):
    IGNORED = 0
    OK = 1
    WARN = 2
    ALERT = 3