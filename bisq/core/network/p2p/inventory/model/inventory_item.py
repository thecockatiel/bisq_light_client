from enum import Enum
from typing import TYPE_CHECKING, Collection, Dict, List, Optional

from bisq.core.network.p2p.inventory.model.deviation_by_integer_diff import (
    DeviationByIntegerDiff,
)
from bisq.core.network.p2p.inventory.model.deviation_by_percentage import (
    DeviationByPercentage,
)
from bisq.core.network.p2p.inventory.model.deviation_of_hashes import DeviationOfHashes
from bisq.core.network.p2p.inventory.model.deviation_severity import DeviationSeverity
from bisq.core.network.p2p.inventory.model.deviation_type import DeviationType

if TYPE_CHECKING:
    from bisq.core.network.p2p.inventory.model.request_info import RequestInfo


class InventoryItem(Enum):
    # Percentage deviation
    OFFER_PAYLOAD = (
        "OfferPayload",
        True,
        DeviationByPercentage(0.5, 1.5, 0.75, 1.25),
        10,
    )
    MAILBOX_STORAGE_PAYLOAD = (
        "MailboxStoragePayload",
        True,
        DeviationByPercentage(0.9, 1.1, 0.95, 1.05),
        2,
    )
    TRADE_STATISTICS3 = (
        "TradeStatistics3",
        True,
        DeviationByPercentage(0.9, 1.1, 0.95, 1.05),
        2,
    )
    ACCOUNT_AGE_WITNESS = (
        "AccountAgeWitness",
        True,
        DeviationByPercentage(0.9, 1.1, 0.95, 1.05),
        2,
    )
    SIGNED_WITNESS = (
        "SignedWitness",
        True,
        DeviationByPercentage(0.9, 1.1, 0.95, 1.05),
        2,
    )

    # Should be same value
    ALERT = ("Alert", True, DeviationByIntegerDiff(1, 1), 2)
    FILTER = ("Filter", True, DeviationByIntegerDiff(1, 1), 2)
    MEDIATOR = ("Mediator", True, DeviationByIntegerDiff(1, 1), 2)
    REFUND_AGENT = ("RefundAgent", True, DeviationByIntegerDiff(1, 1), 2)

    # Should be very close values
    TEMP_PROPOSAL_PAYLOAD = (
        "TempProposalPayload",
        True,
        DeviationByIntegerDiff(3, 5),
        2,
    )
    PROPOSAL_PAYLOAD = ("ProposalPayload", True, DeviationByIntegerDiff(1, 2), 2)
    BLIND_VOTE_PAYLOAD = ("BlindVotePayload", True, DeviationByIntegerDiff(1, 2), 2)

    # Should be very close values
    DAO_STATE_CHAIN_HEIGHT = (
        "daoStateChainHeight",
        True,
        DeviationByIntegerDiff(2, 4),
        3,
    )
    NUM_BSQ_BLOCKS = ("numBsqBlocks", True, DeviationByIntegerDiff(2, 4), 3)

    # Has to be same values at same block
    DAO_STATE_HASH = ("daoStateHash", False, DeviationOfHashes(), 1)
    PROPOSAL_HASH = ("proposalHash", False, DeviationOfHashes(), 1)
    BLIND_VOTE_HASH = ("blindVoteHash", False, DeviationOfHashes(), 1)

    # Percentage deviation
    MAX_CONNECTIONS = (
        "maxConnections",
        True,
        DeviationByPercentage(0.33, 3, 0.4, 2.5),
        2,
    )
    NUM_CONNECTIONS = ("numConnections", True, DeviationByPercentage(0, 3, 0, 2.5), 2)
    PEAK_NUM_CONNECTIONS = (
        "peakNumConnections",
        True,
        DeviationByPercentage(0, 3, 0, 2.5),
        2,
    )
    NUM_ALL_CONNECTIONS_LOST_EVENTS = (
        "numAllConnectionsLostEvents",
        True,
        DeviationByIntegerDiff(1, 2),
        1,
    )
    SENT_BYTES_PER_SEC = ("sentBytesPerSec", True, DeviationByPercentage(), 5)
    RECEIVED_BYTES_PER_SEC = ("receivedBytesPerSec", True, DeviationByPercentage(), 5)
    RECEIVED_MESSAGES_PER_SEC = (
        "receivedMessagesPerSec",
        True,
        DeviationByPercentage(),
        5,
    )
    SENT_MESSAGES_PER_SEC = ("sentMessagesPerSec", True, DeviationByPercentage(), 5)

    # No deviation check
    SENT_BYTES = ("sentBytes", True)
    RECEIVED_BYTES = ("receivedBytes", True)

    # No deviation check
    VERSION = ("version", False)
    COMMIT_HASH = ("commitHash", False)
    USED_MEMORY = ("usedMemory", True)
    JVM_START_TIME = ("jvmStartTime", True)
    FILTERED_SEEDS = ("filteredSeeds", False)

    def __init__(
        self,
        key: str,
        is_number_value: bool,
        deviation_type: Optional[DeviationType] = None,
        deviation_tolerance: int = 1,
    ):
        self.key = key
        self.is_number_value = is_number_value
        self.deviation_type = deviation_type
        # The number of past requests we check to see if there have been repeated alerts or warnings. The higher the
        # number the more repeated alert need to have happened to cause a notification alert.
        # Smallest number is 1, as that takes only the last request data and does not look further back.
        self.deviation_tolerance = deviation_tolerance

    def get_deviation_and_average(
        self, average_values: Dict["InventoryItem", float], value: Optional[str]
    ):
        if self in average_values and value is not None:
            average_value = average_values[self]
            return (self.get_deviation(value, average_value), average_value)
        return None

    def get_deviation(self, value: Optional[str], average: float):
        if (
            self.deviation_type is not None
            and value is not None
            and average != 0
            and self.is_number_value
        ):
            return float(value) / average
        return None

    def get_deviation_severity(
        self,
        deviation: Optional[float],
        collection: Collection[List["RequestInfo"]],
        value: Optional[str],
        current_block_height: str,
    ) -> DeviationSeverity:
        if self.deviation_type is None or deviation is None or value is None:
            return DeviationSeverity.OK

        if isinstance(self.deviation_type, DeviationByPercentage):
            return self.deviation_type.get_deviation_severity(deviation)
        elif isinstance(self.deviation_type, DeviationByIntegerDiff):
            return self.deviation_type.get_deviation_severity(collection, value, self)
        elif isinstance(self.deviation_type, DeviationOfHashes):
            return self.deviation_type.get_deviation_severity(
                collection, value, self, current_block_height
            )
        else:
            return DeviationSeverity.OK
        
    @classmethod
    def get_cls(cls):
        return cls

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def from_key(cls, key: str):
        for item in cls:
            if item.key == key:
                return item
        raise ValueError(f"Unknown key: {key}")