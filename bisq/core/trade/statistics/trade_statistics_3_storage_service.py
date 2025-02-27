from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.network.p2p.persistence.historical_data_store_service import (
    HistoricalDataStoreService,
)
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3
from bisq.core.trade.statistics.trade_statistics_3_store import TradeStatistics3Store


class TradeStatistics3StorageService(
    HistoricalDataStoreService["TradeStatistics3Store"]
):
    FILE_NAME = "TradeStatistics3Store"

    def get_file_name(self):
        return TradeStatistics3StorageService.FILE_NAME

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK
        )

    def can_handle(self, payload: "PersistableNetworkPayload"):
        return isinstance(payload, TradeStatistics3)

    def create_store(self):
        return TradeStatistics3Store()

    def persist_now(self):
        self.persistence_manager.persist_now(lambda: None)
