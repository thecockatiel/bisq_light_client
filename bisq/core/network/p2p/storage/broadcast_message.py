from abc import ABC

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

class BroadcastMessage(NetworkEnvelope, ABC):
    def __init__(self, message_version: int):
        super().__init__(message_version)

    def __eq__(self, other):
        if not isinstance(other, BroadcastMessage):
            return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()