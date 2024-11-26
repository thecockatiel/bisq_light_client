
from enum import IntEnum


class OfferState(IntEnum):
    UNKNOWN = 0
    OFFER_FEE_PAID = 1
    AVAILABLE = 2
    NOT_AVAILABLE = 3
    REMOVED = 4
    MAKER_OFFLINE = 5