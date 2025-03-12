from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING

from bisq.core.dao.burningman.accounting.balance.burned_bsq_balance_entry import (
    BurnedBsqBalanceEntry,
)
from bisq.core.dao.burningman.accounting.balance.monthly_balance_entry import (
    MonthlyBalanceEntry,
)
from bisq.core.dao.burningman.accounting.balance.monthly_burned_bsq_balance_entry import (
    MonthlyBurnedBsqBalanceEntry,
)
from bisq.core.dao.burningman.accounting.balance.balance_entry_type import (
    BalanceEntryType,
)
from bisq.core.dao.burningman.burning_man_accounting_const import BurningManAccountingConst


if TYPE_CHECKING:
    from bisq.core.dao.burningman.accounting.balance.base_balance_entry import (
        BaseBalanceEntry,
    )
    from bisq.core.dao.burningman.model.burning_man_candidate import BurningManCandidate
    from bisq.core.dao.burningman.model.burn_output_model import BurnOutputModel
    from bisq.core.dao.burningman.accounting.balance.received_btc_balance_entry import (
        ReceivedBtcBalanceEntry,
    )


class BalanceModel:

    def __init__(self):
        self._received_btc_balance_entries: set["ReceivedBtcBalanceEntry"] = set()
        self._received_btc_balance_entries_by_month: dict[
            datetime, set["ReceivedBtcBalanceEntry"]
        ] = {}

    def add_received_btc_balance_entry(self, balance_entry: "ReceivedBtcBalanceEntry"):
        self._received_btc_balance_entries.add(balance_entry)

        month = balance_entry.month
        if month not in self._received_btc_balance_entries_by_month:
            self._received_btc_balance_entries_by_month[month] = set()
        self._received_btc_balance_entries_by_month[month].add(balance_entry)

    @property
    def received_btc_balance_entries(self):
        return self._received_btc_balance_entries

    def get_received_btc_balance_entries_by_month(self, month: datetime):
        return self._received_btc_balance_entries_by_month.get(month, set())

    def get_burned_bsq_balance_entries_stream(
        self, burn_output_models: set["BurnOutputModel"]
    ):
        return (
            BurnedBsqBalanceEntry(
                burn_output_model.tx_id,
                burn_output_model.amount,
                datetime.fromtimestamp(burn_output_model.date / 1000),
            )
            for burn_output_model in burn_output_models
        )

    def get_burned_bsq_balance_entries(
        self, burn_output_models: set["BurnOutputModel"]
    ):
        return (
            BurnedBsqBalanceEntry(
                burn_output_model.tx_id,
                burn_output_model.amount,
                datetime.fromtimestamp(burn_output_model.date / 1000),
            )
            for burn_output_model in burn_output_models
        )

    def get_monthly_balance_entries(
        self,
        burning_man_candidate: "BurningManCandidate",
        predicate: Callable[["BaseBalanceEntry"], bool],
    ):
        burn_output_models_by_month = burning_man_candidate.burn_output_models_by_month
        months = self._get_months(
            datetime.now(),
            # we avoid importing BurningManAccountingService because of circular imports
            BurningManAccountingConst.EARLIEST_DATE_YEAR,
            BurningManAccountingConst.EARLIEST_DATE_MONTH,
        )
        monthly_balance_entries = []

        for month in months:
            sum_burned_bsq = 0
            types = set["BalanceEntryType"]()
            if month in burn_output_models_by_month:
                burn_output_models = burn_output_models_by_month[month]
                monthly_burned_bsq_balance_entries = {
                    MonthlyBurnedBsqBalanceEntry(
                        burn_output_model.tx_id,
                        burn_output_model.amount,
                        month,
                    )
                    for burn_output_model in burn_output_models
                }
                for entry in monthly_burned_bsq_balance_entries:
                    if predicate(entry):
                        types.add(entry.type)
                        sum_burned_bsq += entry.amount

            sum_received_btc = 0
            if month in self._received_btc_balance_entries_by_month:
                for entry in self._received_btc_balance_entries_by_month[month]:
                    if predicate(entry):
                        types.add(entry.type)
                        sum_received_btc += entry.amount

            if sum_burned_bsq > 0 or sum_received_btc > 0:
                monthly_balance_entries.append(
                    MonthlyBalanceEntry(sum_received_btc, sum_burned_bsq, month, types)
                )

        return monthly_balance_entries

    def _get_months(self, from_date: datetime, to_year: int, to_month: int):
        """months (1-12)"""
        months = set[datetime]()

        while from_date.year > to_year or (
            from_date.year == to_year and from_date.month > to_month
        ):
            months.add(datetime(from_date.year, from_date.month, 1))
            if from_date.month == 1:
                from_date = from_date.replace(year=from_date.year - 1, month=12)
            else:
                from_date = from_date.replace(month=from_date.month - 1)

        return months

    def __eq__(self, value):
        return (
            isinstance(value, BalanceModel)
            and self._received_btc_balance_entries
            == value._received_btc_balance_entries
            and self._received_btc_balance_entries_by_month
            == value._received_btc_balance_entries_by_month
        )
