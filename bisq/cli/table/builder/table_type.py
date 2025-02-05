from enum import IntEnum, auto


class TableType(IntEnum):
    """
    Used as param in TableBuilder constructor instead of inspecting
    protos to find out what kind of CLI output table should be built.
    """

    ADDRESS_BALANCE_TBL = auto()
    BSQ_BALANCE_TBL = auto()
    BTC_BALANCE_TBL = auto()
    CLOSED_TRADES_TBL = auto()
    FAILED_TRADES_TBL = auto()
    OFFER_TBL = auto()
    OPEN_TRADES_TBL = auto()
    PAYMENT_ACCOUNT_TBL = auto()
    TRADE_DETAIL_TBL = auto()
    TRANSACTION_TBL = auto()
