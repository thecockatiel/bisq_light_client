from enum import Enum
from bisq.common.protocol.proto_util import ProtoUtil
import pb_pb2 as protobuf

class AvailabilityResult(Enum):
    UNKNOWN_FAILURE = "Cannot take offer for unknown reason"
    AVAILABLE = "Offer is available"
    OFFER_TAKEN = "Offer is taken"
    PRICE_OUT_OF_TOLERANCE = "Cannot take offer because taker's price is outside tolerance"
    MARKET_PRICE_NOT_AVAILABLE = "Cannot take offer because market price for calculating trade price is unavailable"
    NO_ARBITRATORS = "Cannot take offer because no arbitrators are available"  # Unused
    NO_MEDIATORS = "Cannot take offer because no mediators are available"
    USER_IGNORED = "Cannot take offer because user is ignored"
    MISSING_MANDATORY_CAPABILITY = "Missing mandatory capability"  # Unused
    NO_REFUND_AGENTS = "Cannot take offer because no refund agents are available"  # Unused
    UNCONF_TX_LIMIT_HIT = "Cannot take offer because you have too many unconfirmed transactions at this moment"
    MAKER_DENIED_API_USER = "Cannot take offer because maker is api user"
    PRICE_CHECK_FAILED = "Cannot take offer because trade price check failed"
    INVALID_SNAPSHOT_HEIGHT = "Cannot take offer because snapshot height does not match. Probably your DAO data are not synced."

    @staticmethod
    def from_proto(proto: 'protobuf.AvailabilityResult'):
        return ProtoUtil.enum_from_proto(AvailabilityResult, protobuf.AvailabilityResult, proto)

    @staticmethod
    def to_proto_message(result: 'AvailabilityResult'):
        return ProtoUtil.proto_enum_from_enum(protobuf.AvailabilityResult, result)
    
    def __init__(self, description: str):
        self.description = description

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def __str__(self):
        return self._name_
