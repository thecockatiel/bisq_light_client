from abc import ABC
from dataclasses import dataclass
from datetime import timedelta

from bisq.core.support.messages.support_message import SupportMessage
from bisq.core.support.support_type import SupportType


@dataclass(kw_only=True)
class DisputeMessage(SupportMessage, ABC):
    TTL = int(timedelta(days=15).total_seconds() * 1000)

    def get_ttl(self) -> int:
        return self.TTL
