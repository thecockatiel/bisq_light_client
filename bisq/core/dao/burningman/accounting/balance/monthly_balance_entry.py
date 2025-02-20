from datetime import datetime
from bisq.common.util.date_util import DateUtil
from bisq.core.dao.burningman.accounting.balance.balance_entry import BalanceEntry
from bisq.core.dao.burningman.accounting.balance.balance_entry_type import (
    BalanceEntryType,
)


class MonthlyBalanceEntry(BalanceEntry):
    def __init__(
        self,
        received_btc: int,
        burned_bsq: int,
        date: datetime,
        types: set[BalanceEntryType],
    ):
        self.received_btc = received_btc
        self.burned_bsq = burned_bsq
        self._date = date
        self._month = DateUtil.get_start_of_month(date)
        self.types = types

    @property
    def date(self):
        return self._date

    @property
    def month(self):
        return self._month
