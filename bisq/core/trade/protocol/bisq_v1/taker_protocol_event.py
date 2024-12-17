

from enum import EnumMeta, IntEnum
from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent

class _CombinedMeta(EnumMeta, type(FluentProtocolEvent)):
    pass

class TakerProtocolEvent(IntEnum, metaclass=_CombinedMeta):
    TAKE_OFFER = 0

