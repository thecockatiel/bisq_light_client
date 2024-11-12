# TODO: THIS CLASS IS INCOMPLETE. made to work with DefaultSeedNodeRepository

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from utils.dir import user_data_dir

@dataclass(kw_only=True)
class Config:
    # Constants
    APP_DATA_DIR_VALUE: ClassVar[Path] = None
    DEFAULT_CONFIG_FILE_NAME = "bisq.properties"
    
    
    # Fields
    seed_nodes: list = field(default_factory=list)
    filter_provided_seed_nodes: list = field(default_factory=list)
    banned_seed_nodes: list = field(default_factory=list)
    app_data_dir: Path = field(default_factory=user_data_dir)
    msg_throttle_per_sec: int = field(default=200)
    msg_throttle_per_10_sec: int = field(default=1000)
    send_msg_throttle_trigger: int = field(default=20)
    send_msg_throttle_sleep: int = field(default=50)
    
    # Properties derived from options but not exposed as options themselves
    tor_dir: Path = field(default=None, init=False)
    storage_dir: Path = field(default=None, init=False)
    key_storage_dir: Path = field(default=None, init=False)
    wallet_dir: Path = field(default=None, init=False)
    
    def __post_init__(self):
        # NOTE: for compability with old code we use the same directory structure as before
        # and we only support btc_mainnet for now
        btc_network_dir = self.app_data_dir.joinpath("btc_mainnet")
        btc_network_dir.mkdir(parents=True, exist_ok=True)
        
        self.key_storage_dir = btc_network_dir.joinpath("keys")
        self.key_storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.storage_dir = btc_network_dir.joinpath("db")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.tor_dir = btc_network_dir.joinpath("tor")
        self.tor_dir.mkdir(parents=True, exist_ok=True)
        
        self.wallet_dir = btc_network_dir.joinpath("wallet")
        self.wallet_dir.mkdir(parents=True, exist_ok=True)
        
        Config.APP_DATA_DIR_VALUE = self.app_data_dir
        
    

CONFIG = Config()