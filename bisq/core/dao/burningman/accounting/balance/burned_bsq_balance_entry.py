from datetime import datetime
from bisq.core.dao.burningman.accounting.balance.balance_entry_type import (
    BalanceEntryType,
)
from bisq.core.dao.burningman.accounting.balance.base_balance_entry import (
    BaseBalanceEntry,
)


class BurnedBsqBalanceEntry(BaseBalanceEntry):
    def __init__(self, tx_id: str, amount: int, date: datetime):
        super().__init__(tx_id, amount, date, BalanceEntryType.BURN_TX)
