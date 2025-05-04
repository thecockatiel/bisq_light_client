from collections.abc import Callable, Collection
from concurrent.futures import ThreadPoolExecutor
import contextvars
from bisq.common.setup.log_setup import get_ctx_logger
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.persistence.append_only_data_store_listener import (
    AppendOnlyDataStoreListener,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.offer.availability.dispute_agent_selection import DisputeAgentSelection
from bisq.core.trade.statistics.trade_statistics_2 import TradeStatistics2
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.trade.statistics.trade_statistics_2_storage_service import (
        TradeStatistics2StorageService,
    )
    from bisq.core.trade.statistics.trade_statistics_3_storage_service import (
        TradeStatistics3StorageService,
    )
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.persistence.append_only_data_store_service import (
        AppendOnlyDataStoreService,
    )
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
        PersistableNetworkPayload,
    )


class TradeStatisticsConverter:

    def __init__(
        self,
        p2p_service: "P2PService",
        p2p_data_storage: "P2PDataStorage",
        trade_statistics_2_storage_service: "TradeStatistics2StorageService",
        trade_statistics_3_storage_service: "TradeStatistics3StorageService",
        append_only_data_store_service: "AppendOnlyDataStoreService",
        storage_dir: Path,
    ):
        self.logger = get_ctx_logger(__name__)
        self._subscriptions: list[Callable[[], None]] = []
        self._trade_statistics_2_storage_service = trade_statistics_2_storage_service
        self._append_only_data_store_service = append_only_data_store_service
        self._append_only_data_store_service.add_service(
            trade_statistics_2_storage_service
        )

        self._executor: Optional["ThreadPoolExecutor"] = None

        trade_statistics_2_store = storage_dir.joinpath("TradeStatistics2Store")

        class Listener(BootstrapListener):

            def on_tor_node_ready(self_):
                if not trade_statistics_2_store.exists():
                    return

                self._executor = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="TradeStatisticsConverter"
                )

                def migrate_v2_data():
                    # We convert early once tor is initialized but still not ready to receive data
                    temp_map: dict["StorageByteArray", "PersistableNetworkPayload"] = {}
                    trade_statistics_3_list = TradeStatisticsConverter.convert_to_trade_statistics_3_list(
                        trade_statistics_2_storage_service.get_map_of_all_data().values()
                    )
                    for st in trade_statistics_3_list:
                        temp_map[StorageByteArray(st.get_hash())] = st

                    # We map to user thread to avoid potential threading issues
                    UserThread.execute(
                        lambda: (
                            trade_statistics_3_storage_service.get_map_of_live_data().update(
                                temp_map
                            ),
                            trade_statistics_3_storage_service.persist_now(),
                        )
                    )

                    try:
                        print(
                            "We delete now the old trade statistics file as it was converted to the new format."
                        )
                        trade_statistics_2_store.unlink(missing_ok=True)
                    except Exception as e:
                        self.logger.error(e, exc_info=e)

                ctx = contextvars.copy_context()
                self._executor.submit(ctx.run, migrate_v2_data)

            def on_data_received(self_):
                pass

        self._subscriptions.append(p2p_service.add_p2p_service_listener(Listener()))

        # We listen to old TradeStatistics2 objects, convert and store them and rebroadcast
        class DataListener(AppendOnlyDataStoreListener):
            def on_added(self_, payload):
                if isinstance(payload, TradeStatistics2):
                    trade_statistics_3 = (
                        TradeStatisticsConverter.convert_to_trade_statistics_3(payload)
                    )
                    # We add it to the p2PDataStorage, which handles to get the data stored in the maps and maybe
                    # re-broadcast as tradeStatistics3 object if not already received.
                    p2p_data_storage.add_persistable_network_payload(
                        trade_statistics_3, None, True
                    )

        self._subscriptions.append(
            p2p_data_storage.add_append_only_data_store_listener(DataListener())
        )

    def shut_down(self):
        if self._executor:
            self._executor.shutdown()
            self._executor = None
        self._append_only_data_store_service.remove_service(
            self._trade_statistics_2_storage_service
        )
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

    @staticmethod
    def convert_to_trade_statistics_3_list(
        persistable_network_payloads: Collection["PersistableNetworkPayload"],
    ) -> list["TradeStatistics3"]:
        result_list: list["TradeStatistics3"] = []
        ts = get_time_ms()

        # We might have duplicate entries from both traders as the trade date was different from old clients.
        # This should not be the case with converting old persisted data as we did filter those out but it is the case
        # when we receive old trade stat objects from the network of 2 not updated traders.
        # The hash was ignoring the trade date so we use that to get a unique list
        map_without_duplicates: dict["StorageByteArray", "TradeStatistics2"] = {}

        for payload in persistable_network_payloads:
            if isinstance(payload, TradeStatistics2) and payload.is_valid():
                map_without_duplicates[StorageByteArray(payload.get_hash())] = payload

        logger = get_ctx_logger(__name__)
        logger.info(
            f"We convert the existing {len(map_without_duplicates)} trade statistics objects to the new format."
        )

        for trade_stats_2 in map_without_duplicates.values():
            trade_stats_3 = TradeStatisticsConverter.convert_to_trade_statistics_3(
                trade_stats_2
            )
            if trade_stats_3.is_valid():
                result_list.append(trade_stats_3)

        size = len(result_list)
        logger.info(
            f"Conversion to {size} new trade statistic objects has been completed after {get_time_ms() - ts} ms"
        )

        # We prune mediator and refundAgent data from all objects but the last 100 as we only use the
        # last 100 entries (DisputeAgentSelection.LOOK_BACK_RANGE).
        result_list.sort(key=lambda x: x.date)

        if size > DisputeAgentSelection.LOOK_BACK_RANGE:
            start = size - DisputeAgentSelection.LOOK_BACK_RANGE
            for i in range(start, size):
                trade_statistics_3 = result_list[i]
                trade_statistics_3.prune_optional_data()

        return result_list

    @staticmethod
    def convert_to_trade_statistics_3(
        trade_statistics_2: TradeStatistics2,
    ) -> TradeStatistics3:
        extra_data_map = trade_statistics_2.extra_data_map
        mediator = (
            extra_data_map.get(TradeStatistics2.MEDIATOR_ADDRESS, None)
            if extra_data_map
            else None
        )
        refund_agent = (
            extra_data_map.get(TradeStatistics2.REFUND_AGENT_ADDRESS, None)
            if extra_data_map
            else None
        )
        time = trade_statistics_2.trade_date
        # We need to avoid that we duplicate tradeStatistics2 objects in case both traders have not updated yet.
        # Before v1.4.0 both traders published the trade statistics. If one trader has updated he will check
        # the capabilities of the peer and if the peer has not updated he will leave publishing to the peer, so we
        # do not have the problem of duplicated objects.
        # Also at conversion of locally stored old trade statistics we need to avoid duplicated entries.
        # To ensure we add only one object we will use the hash of the tradeStatistics2 object which is the same
        # for both traders as it excluded the trade date which is different for both.
        hash_bytes = trade_statistics_2.get_hash()

        return TradeStatistics3(
            trade_statistics_2.get_currency_code(),
            trade_statistics_2.get_trade_price().get_value(),
            trade_statistics_2.get_trade_amount().get_value(),
            trade_statistics_2.offer_payment_method,
            time,
            mediator,
            refund_agent,
            None,
            hash_bytes,
        )
