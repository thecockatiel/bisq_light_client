from collections.abc import Callable
import contextvars
from datetime import datetime
import threading
from typing import TYPE_CHECKING, Optional
from bisq.common.user_thread import UserThread
from bisq.common.util.math_utils import MathUtils
from bisq.core.dao.burningman.accounting.balance.balance_entry_type import (
    BalanceEntryType,
)
from bisq.core.dao.burningman.accounting.balance.received_btc_balance_entry import (
    ReceivedBtcBalanceEntry,
)
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx_type import (
    AccountingTxType,
)
from bisq.core.dao.burningman.burning_man_accounting_const import (
    BurningManAccountingConst,
)
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.monetary.price import Price
from bisq.core.util.average_price_util import get_average_price_tuple
from bitcoinj.base.coin import Coin
from utils.data import SimpleProperty
from bisq.core.dao.burningman.accounting.balance.balance_model import BalanceModel

if TYPE_CHECKING:
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )
    from bisq.core.dao.burningman.accounting.storage.burning_man_accounting_store_service import (
        BurningManAccountingStoreService,
    )
    from bisq.core.dao.burningman.burning_man_presentation_service import (
        BurningManPresentationService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.user.preferences import Preferences
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
        AccountingBlock,
    )


class BurningManAccountingService(DaoSetupService, DaoStateListener):
    """
    Provides APIs for the accounting related aspects of burningmen.
    Combines the received funds from BTC trade fees and DPT payouts and the burned BSQ.
    """

    # Constants moved to BurningManAccountingConst

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        burning_man_accounting_store_service: "BurningManAccountingStoreService",
        burning_man_presentation_service: "BurningManPresentationService",
        trade_statistics_manager: "TradeStatisticsManager",
        preferences: "Preferences",
    ):
        self.dao_state_service = dao_state_service
        self._burning_man_accounting_store_service = (
            burning_man_accounting_store_service
        )
        self._burning_man_presentation_service = burning_man_presentation_service
        self._trade_statistics_manager = trade_statistics_manager
        self._preferences = preferences

        self._average_bsq_price_by_month: dict[datetime, Price] = (
            BurningManAccountingService._get_historical_average_bsq_price_by_month()
        )
        self._average_prices_valid = False
        self.balance_model_by_burning_man_name: dict[str, "BalanceModel"] = {}
        self.is_processing = SimpleProperty(False)

        # cache
        self.received_btc_balance_entry_list_excluding_legacy_bm: list[
            "ReceivedBtcBalanceEntry"
        ] = []
        self._subscriptions: list[Callable[[], None]] = []

        dao_state_service.add_dao_state_listener(self)
        last_block = dao_state_service.last_block
        if last_block:
            self._apply_block(last_block)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._subscriptions.append(
            self._trade_statistics_manager.observable_trade_statistics_set.add_listener(
                lambda _: setattr(self, "_average_prices_valid", False)
            )
        )

    def start(self):
        UserThread.execute(lambda: self.is_processing.set(True))

        self._update_balance_model_by_address()

        def run_async():
            map: dict[str, "BalanceModel"] = {}
            # add_accounting_block_to_balance_model takes about 500ms for 100k items, so we run it in a non UI thread.
            self._burning_man_accounting_store_service.for_each_block(
                lambda block: self._add_accounting_block_to_balance_model(map, block)
            )
            UserThread.execute(
                lambda: self.balance_model_by_burning_man_name.update(map)
            )

        ctx = contextvars.copy_context()
        threading.Thread(
            target=ctx.run,
            args=(run_async,),
            name="BurningManAccountingService.start.run_async",
        ).start()

    def shut_down(self):
        self._burning_man_presentation_service.shut_down()
        self._burning_man_accounting_store_service.shut_down()
        self.dao_state_service.remove_dao_state_listener(self)
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self._apply_block(block)

    def _apply_block(self, block: "Block"):
        self.received_btc_balance_entry_list_excluding_legacy_bm.clear()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_initial_block_requests_complete(self):
        self._update_balance_model_by_address()
        self._burning_man_accounting_store_service.for_each_block(
            self.add_accounting_block_to_balance_model
        )
        UserThread.execute(lambda: self.is_processing.set(False))

    def on_new_block_received(self, accounting_block: "AccountingBlock"):
        self._update_balance_model_by_address()
        self.add_accounting_block_to_balance_model(accounting_block)

    def add_block(self, block: "AccountingBlock"):
        self._burning_man_accounting_store_service.add_if_new_block(block)

    def get_block_height_of_last_block(self) -> int:
        last_block = self.get_last_block()
        return (
            last_block.height
            if last_block
            else BurningManAccountingConst.EARLIEST_BLOCK_HEIGHT - 1
        )

    def get_last_block(self) -> Optional["AccountingBlock"]:
        return self._burning_man_accounting_store_service.get_last_block()

    def get_block_at_height(self, height: int) -> Optional["AccountingBlock"]:
        return self._burning_man_accounting_store_service.get_block_at_height(height)

    def get_average_bsq_price_by_month(self) -> dict[datetime, Price]:
        if not self._average_prices_valid:
            # Fill the map from now back to the last entry of the historical data (April 2019-Nov. 2022).
            self._average_bsq_price_by_month.update(
                self._get_average_bsq_price_by_month(
                    datetime.now(),
                    BurningManAccountingConst.HIST_BSQ_PRICE_LAST_DATE_YEAR,
                    BurningManAccountingConst.HIST_BSQ_PRICE_LAST_DATE_MONTH,
                )
            )
            self._average_prices_valid = True
        return self._average_bsq_price_by_month

    def get_total_amount_of_distributed_btc(self) -> int:
        return sum(
            entry.amount
            for entry in self._get_received_btc_balance_entry_list_excluding_legacy_bm()
        )

    def get_total_amount_of_distributed_btc_fees(self) -> int:
        return sum(
            entry.amount
            for entry in self._get_received_btc_balance_entry_list_excluding_legacy_bm()
            if entry.type == BalanceEntryType.BTC_TRADE_FEE_TX
        )

    def get_total_amount_of_distributed_btc_fees_as_bsq(self) -> int:
        average_bsq_price_by_month = self.get_average_bsq_price_by_month()
        return sum(
            self._received_btc_as_bsq(entry, average_bsq_price_by_month)
            for entry in self._get_received_btc_balance_entry_list_excluding_legacy_bm()
            if entry.type == BalanceEntryType.BTC_TRADE_FEE_TX
        )

    def get_total_amount_of_distributed_dpt(self) -> int:
        return sum(
            entry.amount
            for entry in self._get_received_btc_balance_entry_list_excluding_legacy_bm()
            if entry.type == BalanceEntryType.DPT_TX
        )

    def get_total_amount_of_distributed_dpt_as_bsq(self) -> int:
        average_bsq_price_by_month = self.get_average_bsq_price_by_month()
        return sum(
            self._received_btc_as_bsq(entry, average_bsq_price_by_month)
            for entry in self._get_received_btc_balance_entry_list_excluding_legacy_bm()
            if entry.type == BalanceEntryType.DPT_TX
        )

    def get_total_amount_of_distributed_bsq(self) -> int:
        average_bsq_price_by_month = self.get_average_bsq_price_by_month()
        return sum(
            self._received_btc_as_bsq(entry, average_bsq_price_by_month)
            for entry in self._get_received_btc_balance_entry_list_excluding_legacy_bm()
        )

    @staticmethod
    def _received_btc_as_bsq(
        balance_entry: "ReceivedBtcBalanceEntry",
        average_bsq_price_by_month: dict[datetime, Price],
    ) -> int:
        month = balance_entry.month
        received_btc = balance_entry.amount
        price = average_bsq_price_by_month.get(month, None)
        if price is None or price.value == 0:
            return 0
        volume = price.get_volume_by_amount(Coin.value_of(received_btc)).value
        return MathUtils.round_double_to_long(
            MathUtils.scale_down_by_power_of_10(volume, 6)
        )

    def _get_received_btc_balance_entry_list_excluding_legacy_bm(
        self,
    ) -> list["ReceivedBtcBalanceEntry"]:
        if self.received_btc_balance_entry_list_excluding_legacy_bm:
            return self.received_btc_balance_entry_list_excluding_legacy_bm

        self.received_btc_balance_entry_list_excluding_legacy_bm.extend(
            entry
            for key, balance_model in self.balance_model_by_burning_man_name.items()
            if key
            not in {
                self._burning_man_presentation_service.LEGACY_BURNING_MAN_DPT_NAME,
                self._burning_man_presentation_service.LEGACY_BURNING_MAN_BTC_FEES_NAME,
            }
            for entry in balance_model.received_btc_balance_entries
        )
        return self.received_btc_balance_entry_list_excluding_legacy_bm

    def get_distributed_btc_balance_by_month(self, month: datetime):
        return (
            e
            for key, entry in self.balance_model_by_burning_man_name.items()
            if key
            not in {
                self._burning_man_presentation_service.LEGACY_BURNING_MAN_DPT_NAME,
                self._burning_man_presentation_service.LEGACY_BURNING_MAN_BTC_FEES_NAME,
            }
            for e in entry.get_received_btc_balance_entries_by_month(month)
        )

    def resync_accounting_data_from_scratch(
        self, result_handler: Callable[[], None]
    ) -> None:
        self._burning_man_accounting_store_service.remove_all_blocks(result_handler)

    def resync_accounting_data_from_resources(self) -> None:
        self._burning_man_accounting_store_service.delete_storage_file()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delegates
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_blocks_at_least_with_height(
        self, min_height: int
    ) -> list["AccountingBlock"]:
        return (
            self._burning_man_accounting_store_service.get_blocks_at_least_with_height(
                min_height
            )
        )

    def get_burning_man_name_by_address(self) -> dict[str, str]:
        return self._burning_man_presentation_service.get_burning_man_name_by_address()

    @property
    def genesis_tx_id(self) -> str:
        return self._burning_man_presentation_service.genesis_tx_id

    def purge_last_ten_blocks(self) -> None:
        self._burning_man_accounting_store_service.purge_last_ten_blocks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _update_balance_model_by_address(self) -> None:
        for (
            key
        ) in (
            self._burning_man_presentation_service.get_burning_man_candidates_by_name().keys()
        ):
            if key not in self.balance_model_by_burning_man_name:
                self.balance_model_by_burning_man_name[key] = BalanceModel()

    def add_accounting_block_to_balance_model(
        self, accounting_block: "AccountingBlock"
    ) -> None:
        self._add_accounting_block_to_balance_model(
            self.balance_model_by_burning_man_name, accounting_block
        )

    def _add_accounting_block_to_balance_model(
        self,
        balance_model_by_burning_man_name: dict[str, "BalanceModel"],
        accounting_block: "AccountingBlock",
    ) -> None:
        for tx in accounting_block.txs:
            for tx_output in tx.outputs:
                name = tx_output.name
                if name not in balance_model_by_burning_man_name:
                    balance_model_by_burning_man_name[name] = BalanceModel()
                balance_model_by_burning_man_name[name].add_received_btc_balance_entry(
                    ReceivedBtcBalanceEntry(
                        tx.truncated_tx_id,
                        tx_output.value,
                        datetime.fromtimestamp(accounting_block.date / 1000),
                        self._to_balance_entry_type(tx.type),
                    )
                )

    def _get_average_bsq_price_by_month(
        self, from_date: datetime, back_to_year: int, back_to_month: int
    ) -> dict[datetime, Price]:
        average_bsq_price_by_month: dict[datetime, Price] = {}

        while from_date.year > back_to_year or (
            from_date.year == back_to_year and from_date.month > back_to_month
        ):
            date = datetime(from_date.year, from_date.month, 1)
            average_bsq_price = get_average_price_tuple(
                self._preferences, self._trade_statistics_manager, 30, date
            )[1]
            average_bsq_price_by_month[date] = average_bsq_price

            if from_date.month == 1:
                from_date = from_date.replace(year=from_date.year - 1, month=12)
            else:
                from_date = from_date.replace(month=from_date.month - 1)

        return average_bsq_price_by_month

    @staticmethod
    def _to_balance_entry_type(tx_type: AccountingTxType) -> BalanceEntryType:
        if tx_type == AccountingTxType.BTC_TRADE_FEE_TX:
            return BalanceEntryType.BTC_TRADE_FEE_TX
        else:
            return BalanceEntryType.DPT_TX

    @staticmethod
    def _get_historical_average_bsq_price_by_month() -> dict[datetime, Price]:
        # We use the average 30 day BSQ price from the first day of a month back 30 days. So for 1.Nov 2022 we take the average during October 2022.
        # Filling the map takes a bit of computation time (about 5 sec), so we use for historical data a pre-calculated list.
        # Average price from 1. May 2019 (April average) - 1. Nov 2022 (Oct average)
        historical = (
            "1648789200000=2735, 1630472400000=3376, 1612155600000=6235, 1559365200000=13139, "
            "1659330000000=3609, 1633064400000=3196, 1583038800000=7578, 1622523600000=3918, "
            "1625115600000=3791, 1667278800000=3794, 1561957200000=10882, 1593579600000=6153, "
            "1577854800000=9034, 1596258000000=6514, 1604206800000=5642, 1643691600000=3021, "
            "1606798800000=4946, 1569906000000=10445, 1567314000000=9885, 1614574800000=5052, "
            "1656651600000=3311, 1638334800000=3015, 1564635600000=8788, 1635742800000=3065, "
            "1654059600000=3207, 1646110800000=2824, 1609477200000=4199, 1664600400000=3820, "
            "1662008400000=3756, 1556686800000=24094, 1588309200000=7986, 1585717200000=7994, "
            "1627794000000=3465, 1580533200000=5094, 1590987600000=7411, 1619845200000=3956, "
            "1617253200000=4024, 1575176400000=9571, 1572584400000=9058, 1641013200000=3052, "
            "1601528400000=5648, 1651381200000=2908, 1598936400000=6032"
        )

        return {
            datetime.fromtimestamp(int(timestamp) / 1000): Price.value_of(
                "BSQ", int(price)
            )
            for timestamp, price in (
                entry.split("=") for entry in historical.split(", ")
            )
        }
