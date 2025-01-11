from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger
from utils.data import SimpleProperty

logger = get_logger(__name__)

# TODO
class WalletsSetup:
    PRE_SEGWIT_BTC_WALLET_BACKUP = "pre_segwit_bisq_BTC.wallet.backup" 
    PRE_SEGWIT_BSQ_WALLET_BACKUP = "pre_segwit_bisq_BSQ.wallet.backup"
    
    def __init__(self, config: "Config"):
        self.params = config.base_currency_network.parameters
        self.num_peers_property = SimpleProperty(0)
        self.download_percentage_property = SimpleProperty(100.0/100.0)
        self.chain_height_property = SimpleProperty(0)
    
    @property
    def is_download_complete(self):
        return True
    
    @property
    def has_sufficient_peers_for_broadcast(self):
        return True
    
    def is_chain_height_synced_within_tolerance(self):
        raise RuntimeError("WalletsSetup.is_chain_height_synced_within_tolerance Not implemented yet")