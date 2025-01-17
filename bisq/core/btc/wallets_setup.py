from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from utils.data import SimpleProperty

if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from bisq.core.btc.setup.wallet_config import WalletConfig
    
logger = get_logger(__name__)

# TODO
class WalletsSetup:
    PRE_SEGWIT_BTC_WALLET_BACKUP = "pre_segwit_bisq_BTC.wallet.backup" 
    PRE_SEGWIT_BSQ_WALLET_BACKUP = "pre_segwit_bisq_BSQ.wallet.backup"
    STARTUP_TIMEOUT_SEC = 180
    BSQ_WALLET_FILE_NAME = "bisq_BSQ.wallet"
    SPV_CHAIN_FILE_NAME = "bisq.spvchain"
    
    def __init__(self, config: "Config"):
        self.config = config
        self.params = config.base_currency_network.parameters
        self.num_peers_property = SimpleProperty(0)
        self.download_percentage_property = SimpleProperty(100.0/100.0)
        self.chain_height_property = SimpleProperty(0)
        self.wallets_setup_failed = SimpleProperty(False)
        self.wallet_config: Optional["WalletConfig"] = None
        self.shut_down_complete = SimpleProperty(False)
    
    @property
    def is_download_complete(self):
        return True
    
    @property
    def has_sufficient_peers_for_broadcast(self):
        return True
    
    def is_chain_height_synced_within_tolerance(self):
        raise RuntimeError("WalletsSetup.is_chain_height_synced_within_tolerance Not implemented yet")
    
    def resync_spv_chain(self):
        self.config.wallet_dir.joinpath(WalletsSetup.SPV_CHAIN_FILE_NAME).unlink(missing_ok=True)

    def get_wallet_config(self):
        return self.wallet_config

    def shut_down(self):
        # TODO
        self.shut_down_complete.set(True)
        pass 
    