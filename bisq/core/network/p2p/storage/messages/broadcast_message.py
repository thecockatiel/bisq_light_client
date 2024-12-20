from abc import ABC
from dataclasses import dataclass

from bisq.common.protocol.network.network_envelope import NetworkEnvelope

@dataclass(kw_only=True)
class BroadcastMessage(NetworkEnvelope, ABC):
    pass