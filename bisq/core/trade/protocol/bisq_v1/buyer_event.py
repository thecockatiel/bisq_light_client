from enum import EnumMeta, IntEnum
from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent


class _CombinedMeta(EnumMeta, type(FluentProtocolEvent)):
    pass


class BuyerEvent(IntEnum, metaclass=_CombinedMeta):
    STARTUP = 0
    PAYMENT_SENT = 1
