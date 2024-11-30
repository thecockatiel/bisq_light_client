
from enum import IntEnum


class DisputeResultReason(IntEnum):
    OTHER = 0
    BUG = 1
    USABILITY = 2
    SCAM = 3                # Not used anymore
    PROTOCOL_VIOLATION = 4  # Not used anymore
    NO_REPLY = 5            # Not used anymore
    BANK_PROBLEMS = 6
    OPTION_TRADE = 7
    SELLER_NOT_RESPONDING = 8
    WRONG_SENDER_ACCOUNT = 9
    TRADE_ALREADY_SETTLED = 10
    PEER_WAS_LATE = 11