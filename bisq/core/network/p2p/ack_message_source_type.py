from enum import IntEnum

class AckMessageSourceType(IntEnum):
    UNDEFINED = 0
    OFFER_MESSAGE = 1
    TRADE_MESSAGE = 2
    ARBITRATION_MESSAGE = 3
    MEDIATION_MESSAGE = 4
    TRADE_CHAT_MESSAGE = 5
    REFUND_MESSAGE = 6
    LOG_TRANSFER = 7