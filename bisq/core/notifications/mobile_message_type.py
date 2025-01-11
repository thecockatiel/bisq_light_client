from enum import IntEnum, auto


class MobileMessageType(IntEnum):

    def _generate_next_value_(name, start, count, last_values):
        return count  # count starts from 0

    SETUP_CONFIRMATION = auto()
    OFFER = auto()
    TRADE = auto()
    DISPUTE = auto()
    PRICE = auto()
    MARKET = auto()
    ERASE = auto()
