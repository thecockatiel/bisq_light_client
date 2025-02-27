from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.core.network.p2p.persistence.map_store_service import MapStoreService
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.trade.statistics.trade_statistics_2 import TradeStatistics2
from bisq.core.trade.statistics.trade_statistics_2_store import TradeStatistics2Store


class TradeStatistics2StorageService(
    MapStoreService["TradeStatistics2Store", "PersistableNetworkPayload"]
):
    FILE_NAME = "TradeStatistics2Store"

    def get_file_name(self):
        return TradeStatistics2StorageService.FILE_NAME

    def initialize_persistence_manager(self):
        self.persistence_manager.initialize(
            self.store, PersistenceManagerSource.NETWORK
        )

    def get_map(self):
        # As it is used for data request and response and we do not want to send any old trade stat data anymore.
        return {}
    
    # We overwrite that method to receive old trade stats from the network. As we deactivated getMap to not deliver
    # hashes we needed to use the get_map_of_all_data method to actually store the data.
    # That's a bit of a hack but it's just for transition and can be removed after a few months anyway.
    # Alternatively we could create a new interface to handle it differently on the other client classes but that
    # seems to be not justified as it is needed only temporarily.
    def put_if_absent(self, hash, payload):
        return self.get_map_of_all_data().setdefault(hash, payload)
    
    def get_map_of_all_data(self):
        return self.store.get_map()

    def can_handle(self, payload: "PersistableNetworkPayload"):
        return isinstance(payload, TradeStatistics2)

    def create_store(self):
        return TradeStatistics2Store()
