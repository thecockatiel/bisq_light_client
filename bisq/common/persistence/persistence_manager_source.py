
from enum import Enum
from datetime import timedelta

class PersistenceManagerSource(Enum):
    # for data stores we received from the network and which could be rebuilt. We store only for avoiding too much network traffic.
    NETWORK = (
        1,
        int(timedelta(minutes=5).total_seconds() * 1000),
        False,
    )  # 5 minutes

    # For data stores which are created from private local data. This data could only be rebuilt from backup files.
    PRIVATE = 10, 200, True

    # For data stores which are created from private local data. Loss of that data would not have critical consequences.
    PRIVATE_LOW_PRIO = 4, int(timedelta(minutes=1).total_seconds() * 1000), False

    def __init__(
        self, num_max_backup_files: int, delay: int, flush_at_shutdown: bool
    ):
        self.num_max_backup_files = num_max_backup_files
        self.delay = delay
        self.flush_at_shutdown = flush_at_shutdown

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj