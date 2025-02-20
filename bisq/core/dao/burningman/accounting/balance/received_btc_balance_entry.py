from datetime import datetime
from bisq.core.dao.burningman.accounting.balance.balance_entry_type import (
    BalanceEntryType,
)
from bisq.core.dao.burningman.accounting.balance.base_balance_entry import (
    BaseBalanceEntry,
)


class ReceivedBtcBalanceEntry(BaseBalanceEntry):

    # We store only last 4 bytes in the AccountTx which is used to create a ReceivedBtcBalanceEntry instance.
    def __init__(
        self,
        truncated_tx_id: bytes,
        amount: int,
        date: datetime,
        entry_type: BalanceEntryType,
    ):
        super().__init__(truncated_tx_id.hex(), amount, date, entry_type)
