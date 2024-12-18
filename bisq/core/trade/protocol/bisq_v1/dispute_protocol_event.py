from enum import EnumMeta, IntEnum
from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent


class _CombinedMeta(EnumMeta, type(FluentProtocolEvent)):
    pass


class DisputeProtocolEvent(IntEnum, metaclass=_CombinedMeta):
    MEDIATION_RESULT_ACCEPTED = 0
    MEDIATION_RESULT_REJECTED = 1
    ARBITRATION_REQUESTED = 2
