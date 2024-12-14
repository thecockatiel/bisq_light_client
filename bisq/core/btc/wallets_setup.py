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