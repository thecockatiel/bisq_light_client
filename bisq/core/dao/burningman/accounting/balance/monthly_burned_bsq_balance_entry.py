from datetime import datetime
from bisq.core.dao.burningman.accounting.balance.burned_bsq_balance_entry import (
    BurnedBsqBalanceEntry,
)


class MonthlyBurnedBsqBalanceEntry(BurnedBsqBalanceEntry):
    def __init__(self, tx_id: str, amount: int, date: datetime):
        super().__init__(tx_id, amount, date)
