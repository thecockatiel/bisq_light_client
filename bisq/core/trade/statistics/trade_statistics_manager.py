from typing import TYPE_CHECKING, Optional
from pathlib import Path
from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.currency_tuple import CurrencyTuple
from bisq.core.locale.currency_util import (
    get_all_sorted_crypto_currencies,
    get_all_sorted_fiat_currencies,
)
from bisq.core.locale.res import Res
from bisq.core.monetary.price import Price
from bisq.core.network.p2p.persistence.append_only_data_store_listener import (
    AppendOnlyDataStoreListener,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.trade.model.bisq_v1.buyer_trade import BuyerTrade
from bisq.core.trade.model.bisq_v1.trade import Trade
from bisq.core.trade.statistics.trade_statistics_2 import TradeStatistics2
from bisq.core.trade.statistics.trade_statistics_for_json import TradeStatisticsForJson
from bisq.core.util.json_util import JsonUtil
from utils.data import ObservableSet
from bisq.common.file.json_file_manager import JsonFileManager
from utils.time import get_time_ms
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3

if TYPE_CHECKING:
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.persistence.append_only_data_store_service import (
        AppendOnlyDataStoreService,
    )
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.statistics.trade_statistics_3_storage_service import (
        TradeStatistics3StorageService,
    )
    from bisq.core.trade.statistics.trade_statistics_converter import (
        TradeStatisticsConverter,
    )

logger = get_logger(__name__)


class TradeStatisticsManager:

    def __init__(
        self,
        p2p_service: "P2PService",
        price_feed_service: "PriceFeedService",
        trade_statistics_3_storage_service: "TradeStatistics3StorageService",
        append_only_data_store_service: "AppendOnlyDataStoreService",
        trade_statistics_converter: "TradeStatisticsConverter",
        storage_dir: Path,
        dump_statistics: bool,
    ):
        self._p2p_service = p2p_service
        self._price_feed_service = price_feed_service
        self._trade_statistics_3_storage_service = trade_statistics_3_storage_service
        self._trade_statistics_converter = trade_statistics_converter
        self._storage_dir = storage_dir
        self._dump_statistics = dump_statistics

        self._json_file_manager: Optional["JsonFileManager"] = None
        self.observable_trade_statistics_set = ObservableSet["TradeStatistics3"]()

        append_only_data_store_service.add_service(trade_statistics_3_storage_service)

    def shut_down(self):
        if self._trade_statistics_converter:
            self._trade_statistics_converter.shut_down()
        if self._json_file_manager:
            self._json_file_manager.shut_down()

    def on_all_services_initialized(self):
        class Listener(AppendOnlyDataStoreListener):
            def on_added(self_, payload):
                if isinstance(payload, TradeStatistics3):
                    if not payload.is_valid():
                        return
                    self.observable_trade_statistics_set.add(payload)
                    self._price_feed_service.set_bisq_market_price(
                        payload.currency, payload.get_trade_price()
                    )
                    self.maybe_dump_statistics()

        self._p2p_service.p2p_data_storage.add_append_only_data_store_listener(
            Listener()
        )

        for (
            entry
        ) in self._trade_statistics_3_storage_service.get_map_of_all_data().values():
            if isinstance(entry, TradeStatistics3) and entry.is_valid():
                self.observable_trade_statistics_set.add(entry)

        # get the most recent price for each ccy and notify priceFeedService
        # (this relies on the trade statistics set being sorted by date)
        newest_price_by_currency: dict[str, "Price"] = {}
        for trade_stat in self.observable_trade_statistics_set:
            currency = trade_stat.currency
            newest_price_by_currency[currency] = trade_stat.get_trade_price()
        self._price_feed_service.apply_initial_bisq_market_price(
            newest_price_by_currency
        )
        self.maybe_dump_statistics()

    def maybe_dump_statistics(self):
        if not self._dump_statistics:
            return

        if self._json_file_manager is None:
            self._json_file_manager = JsonFileManager(self._storage_dir)

            # We only dump once the currencies as they do not change during runtime
            # Dump fiat currencies
            fiat_currency_list = [
                CurrencyTuple(e.code, e.name, 8)
                for e in get_all_sorted_fiat_currencies()
            ]
            self._json_file_manager.write_to_disc_threaded(
                JsonUtil.object_to_json(fiat_currency_list), "fiat_currency_list"
            )

            # Dump crypto currencies
            crypto_currency_list = [
                CurrencyTuple(e.code, e.name, 8)
                for e in get_all_sorted_crypto_currencies()
            ]
            crypto_currency_list.insert(
                0,
                CurrencyTuple(
                    Res.base_currency_code,
                    Res.base_currency_name,
                    8,
                ),
            )
            self._json_file_manager.write_to_disc_threaded(
                JsonUtil.object_to_json(crypto_currency_list), "crypto_currency_list"
            )

            # Filter active currencies
            year_ago = get_time_ms() - 365 * 24 * 60 * 60 * 1000
            active_currencies = {
                e.currency
                for e in self.observable_trade_statistics_set
                if e.date > year_ago
            }

            active_fiat_currency_list = [
                CurrencyTuple(e.code, e.name, 8)
                for e in fiat_currency_list
                if e.code in active_currencies
            ]
            self._json_file_manager.write_to_disc_threaded(
                JsonUtil.object_to_json(active_fiat_currency_list),
                "active_fiat_currency_list",
            )

            active_crypto_currency_list = [
                CurrencyTuple(e.code, e.name, 8)
                for e in crypto_currency_list
                if e.code in active_currencies
            ]
            self._json_file_manager.write_to_disc_threaded(
                JsonUtil.object_to_json(active_crypto_currency_list),
                "active_crypto_currency_list",
            )

        # Dump trade statistics
        trade_statistics_list = sorted(
            (TradeStatisticsForJson(e) for e in self.observable_trade_statistics_set),
            key=lambda x: x.trade_date,
            reverse=True,
        )
        self._json_file_manager.write_to_disc_threaded(
            JsonUtil.object_to_json(trade_statistics_list), "trade_statistics"
        )

    def maybe_republish_trade_statistics(
        self,
        trades: set["TradeModel"],
        referral_id: Optional[str],
        is_tor_network_mode: bool,
    ):
        ts = get_time_ms()
        hashes = self._trade_statistics_3_storage_service.get_map_of_all_data().keys()
        for trade in trades:
            if isinstance(trade, Trade):
                if isinstance(trade, BuyerTrade):
                    logger.debug(
                        f"Trade: {trade.get_short_id()} is a buyer trade, we only republish if we have been seller."
                    )
                    continue

                trade_statistics_3 = TradeStatistics3.from_trade(
                    trade, referral_id, is_tor_network_mode
                )

                if StorageByteArray(trade_statistics_3.get_hash()) in hashes:
                    logger.debug(
                        f"Trade: {trade.get_short_id()}. We already have a tradeStatistics matching the hash of tradeStatistics3."
                    )
                    continue

                # If we did not find a TradeStatistics3 we look up if we find a TradeStatistics3 converted from
                # TradeStatistics2 where we used the original hash, which is not the native hash of the
                # TradeStatistics3 but of TradeStatistics2.
                if not trade.is_bsq_swap:
                    trade_statistics_2 = TradeStatistics2.from_trade(
                        trade, referral_id, is_tor_network_mode
                    )
                    if StorageByteArray(trade_statistics_2.get_hash()) in hashes:
                        logger.debug(
                            f"Trade: {trade.get_short_id()}. We already have a tradeStatistics matching the hash of tradeStatistics2."
                        )
                        continue

                if not trade_statistics_3.is_valid():
                    logger.warning(
                        f"Trade: {trade.get_short_id()}. Trade statistics is invalid. We do not publish it."
                    )
                    continue

                # Publish the trade statistics
                logger.info(
                    f"Trade: {trade.get_short_id()}. We republish tradeStatistics3 as we did not find it in the existing trade statistics."
                )
                self._p2p_service.add_persistable_network_payload(
                    trade_statistics_3, True
                )
        logger.info(
            f"maybe_republish_trade_statistics took {get_time_ms() - ts} ms. Number of tradeStatistics: {len(hashes)}. Number of own trades: {len(trades)}"
        )
