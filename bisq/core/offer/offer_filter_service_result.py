class OfferFilterServiceResult:
    VALID = True
    API_DISABLED = False
    HAS_NO_PAYMENT_ACCOUNT_VALID_FOR_OFFER = False
    HAS_NOT_SAME_PROTOCOL_VERSION = False
    IS_IGNORED = False
    IS_OFFER_BANNED = False
    IS_CURRENCY_BANNED = False
    IS_PAYMENT_METHOD_BANNED = False
    IS_NODE_ADDRESS_BANNED = False
    REQUIRE_UPDATE_TO_NEW_VERSION = False
    IS_INSUFFICIENT_COUNTERPARTY_TRADE_LIMIT = False
    IS_MY_INSUFFICIENT_TRADE_LIMIT = False
    HIDE_BSQ_SWAPS_DUE_DAO_DEACTIVATED = False

    def __init__(self, is_valid: bool = False):
        self.is_valid = is_valid

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
