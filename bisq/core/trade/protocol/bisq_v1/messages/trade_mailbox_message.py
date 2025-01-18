from abc import ABC
from dataclasses import dataclass, field
from datetime import timedelta

from bisq.core.trade.protocol.trade_message import TradeMessage

@dataclass
class TradeMailboxMessage(TradeMessage, ABC):
    # 15 days in milliseconds
    TTL = int(timedelta(days=15).total_seconds() * 1000)

    def __eq__(self, other):
        if not isinstance(other, TradeMailboxMessage):
            return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()

    def __str__(self):
        return f"TradeMailboxMessage(trade_id='{self.trade_id}', uid='{self.uid}', message_version={self.message_version})"