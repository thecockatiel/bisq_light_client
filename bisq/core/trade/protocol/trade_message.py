from abc import ABC
from dataclasses import dataclass
from typing import Optional

from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.uid_message import UidMessage


@dataclass(frozen=True, kw_only=True)
class TradeMessage(NetworkEnvelope, UidMessage, ABC):
    trade_id: str
    uid: str

    def __eq__(self, other):
        if not isinstance(other, TradeMessage):
            return False
        return (
            self.trade_id == other.trade_id
            and self.uid == other.uid
            and self.message_version == other.message_version
        )

    def __hash__(self):
        return hash((self.trade_id, self.uid, self.message_version))

    def __str__(self):
        return f"TradeMessage(trade_id='{self.trade_id}', uid='{self.uid}', message_version={self.message_version})"
