
from enum import IntEnum

from bisq.common.protocol.proto_util import ProtoUtil

# Used for persistence of Cookie. Entries must not be changes or removed. Only adding entries is permitted.
class CookieKey(IntEnum):
    STAGE_X = 0
    STAGE_Y = 1
    STAGE_W = 2
    STAGE_H = 3
    TRADE_STAT_CHART_USE_USD = 4
    CLEAN_TOR_DIR_AT_RESTART = 5
    DELAY_STARTUP = 6
    
    @staticmethod
    def from_proto(proto_value: str):
        return ProtoUtil.enum_from_proto(CookieKey, proto_value)

    def to_proto_message(self):
        return self.name
