from bisq.common.util.date_util import DateUtil
from bisq.core.dao.burningman.accounting.balance.balance_entry import BalanceEntry
from datetime import datetime
from bisq.core.dao.burningman.accounting.balance.balance_entry_type import (
    BalanceEntryType,
)


class BaseBalanceEntry(BalanceEntry):
    def __init__(
        self, tx_id: str, amount: int, date: datetime, entry_type: BalanceEntryType
    ):
        self.tx_id = tx_id
        self.amount = amount
        self._date = date
        self._month = DateUtil.get_start_of_month(date)
        self.type = entry_type

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def month(self) -> datetime:
        return self._month

    def __str__(self) -> str:
        return (
            f"BaseBalanceEntry{{\n"
            f"    txId={self.tx_id},\n"
            f"    amount={self.amount},\n"
            f"    date={self.date},\n"
            f"    month={self.month},\n"
            f"    type={self.type}\n"
            f"}}"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, BaseBalanceEntry):
            return False
        return (
            self.tx_id == other.tx_id
            and self.amount == other.amount
            and self._date == other._date
            and self._month == other._month
            and self.type == other.type
        )

    def __hash__(self):
        return hash(
            (
                self.tx_id,
                self.amount,
                self._date,
                self._month,
                self.type,
            )
        )
