from bisq.common.config.config import Config


# TODO
class WalletsSetup:
    
    def __init__(self, config: "Config"):
        self.params = config.base_currency_network.parameters
    
    @property
    def is_download_complete(self):
        return True
    
    @property
    def has_sufficient_peers_for_broadcast(self):
        return True
    
    def is_chain_height_synced_within_tolerance(self):
        raise RuntimeError("WalletsSetup.is_chain_height_synced_within_tolerance Not implemented yet")