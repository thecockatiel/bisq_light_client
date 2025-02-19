from enum import IntEnum


class AssetState(IntEnum):
    UNDEFINED = 0
    IN_TRIAL_PERIOD = 1
    ACTIVELY_TRADED = 2
    DE_LISTED = 3
    REMOVED_BY_VOTING = 4  # Was removed by voting
