from dataclasses import dataclass, field

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.direct_message import DirectMessage
from bisq.core.network.p2p.uid_message import UidMessage

@dataclass(frozen=True, kw_only=True)
class OfferMessage(NetworkEnvelope, DirectMessage, UidMessage):
    message_version: int
    offer_id: str
    uid: str | None = field(default=None)

    def __post_init__(self):
        if self.uid is not None and not isinstance(self.uid, str):
            raise ValueError("uid must be a string or None")
