from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReimbursementModel:
    amount: int
    height: int
    date: int
    cycle_index: int
    tx_id: str

    def __str__(self):
        return (
            f"\n          ReimbursementModel{{"
            f"\n               amount={self.amount},"
            f"\n               height={self.height},"
            f"\n               date={datetime.fromtimestamp(self.date/1000)},"
            f"\n               cycle_index={self.cycle_index},"
            f"\n               tx_id={self.tx_id}"
            f"\n          }}"
        )
