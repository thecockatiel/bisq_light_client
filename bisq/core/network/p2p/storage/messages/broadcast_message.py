from abc import ABC
from dataclasses import dataclass

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope

@dataclass(frozen=True)
class BroadcastMessage(NetworkEnvelope, ABC):
    pass