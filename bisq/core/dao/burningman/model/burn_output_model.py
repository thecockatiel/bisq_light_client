from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BurnOutputModel:
    amount: int
    decayed_amount: int
    height: int
    tx_id: str
    date: int
    cycle_index: int

    def __str__(self) -> str:
        return (
            f"\n          BurnOutputModel{{"
            f"\n                amount={self.amount},"
            f"\n               decayed_amount={self.decayed_amount},"
            f"\n               height={self.height},"
            f"\n               tx_id='{self.tx_id}',"
            f"\n               date={datetime.fromtimestamp(self.date/1000)},"
            f"\n               cycle_index={self.cycle_index}"
            f"\n          }}"
        )
