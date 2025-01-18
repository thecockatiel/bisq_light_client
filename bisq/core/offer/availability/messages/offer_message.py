from dataclasses import dataclass, field
from typing import Optional

from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.uid_message import UidMessage
from utils.data import raise_required

@dataclass
class OfferMessage(NetworkEnvelope, DirectMessage, UidMessage):
    offer_id: str = field(default_factory=raise_required)
    uid: Optional[str] = field(default=None)

    def __post_init__(self):
        if self.uid is not None and not isinstance(self.uid, str):
            raise ValueError("uid must be a string or None")
