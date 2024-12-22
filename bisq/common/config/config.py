# TODO: THIS CLASS IS INCOMPLETE. made to work with DefaultSeedNodeRepository

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from bisq.common.config.base_currency_network import BaseCurrencyNetwork
from utils.dir import user_data_dir


@dataclass(kw_only=True)
class Config:
    # Constants
    APP_DATA_DIR_VALUE: ClassVar[Path] = None
    DEFAULT_CONFIG_FILE_NAME = "bisq.properties"
    UNSPECIFIED_PORT = -1
    MAX_SEQUENCE_NUMBER_MAP_SIZE_BEFORE_PURGE = 1000

    # Fields
    config_file: Path = field(init=False, default=None)
    ban_list: list[str] = field(default_factory=list)
    seed_nodes: list = field(default_factory=list)
    use_localhost_for_p2p: bool = field(default=False)
    max_connections: int = field(default=12)
    socks5_proxy_btc_address: str = field(default="")
    socks5_proxy_http_address: str = field(default="")
    torrc_file: Path = field(default=None)
    torrc_options: str = field(default="")
    tor_control_host: str = field(default="127.0.0.1")
    tor_control_port: int = field(default=UNSPECIFIED_PORT)
    tor_control_password: str = field(default="")
    filter_provided_seed_nodes: list = field(default_factory=list)
    banned_seed_nodes: list = field(default_factory=list)
    banned_price_relay_nodes: list = field(default_factory=list)
    base_currency_network: BaseCurrencyNetwork = field(default=BaseCurrencyNetwork.BTC_MAINNET)
    referral_id: str = field(default="")
    use_dev_mode: bool = field(default=False)
    use_dev_privilege_keys: bool = field(default=False)
    dump_statistics: bool = field(default=False)
    ignore_dev_msg: bool = field(default=False)
    providers: list[str] = field(default_factory=list)
    app_data_dir: Path = field(default_factory=user_data_dir)
    node_port: int = field(default=9999)
    log_level: str = field(default="INFO")
    msg_throttle_per_sec: int = field(default=200)
    msg_throttle_per_10_sec: int = field(default=1000)
    send_msg_throttle_trigger: int = field(default=20)
    send_msg_throttle_sleep: int = field(default=50)
    use_tor_for_btc: bool = field(default=False)
    use_tor_for_btc_option_set_explicitly: bool = field(default=False)
    btc_nodes: str = field(default="", init=False)
    rpc_user: str = field(default="")
    rpc_password: str = field(default="")
    rpc_block_notification_port: int = field(default=UNSPECIFIED_PORT)
    full_dao_node: bool = field(default=False, init=False)
    full_dao_node_option_set_explicitly: bool = field(default=False, init=False)
    genesis_tx_id: str = field(default="")
    genesis_block_height: int = field(default=-1)
    genesis_total_supply: int = field(default=-1)
    dump_delayed_payout_txs: bool = field(default=False)
    allow_faulty_delayed_txs: bool = field(default=False)
    republish_mailbox_entries: bool = field(default=False)
    is_bm_full_node: bool = field(default=False, init=False)

    # Properties derived from options but not exposed as options themselves
    tor_dir: Path = field(default=None, init=False)
    tor_use_bridges_file: bool = field(default=True, init=False)
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
        Config.config_file = self.app_data_dir.joinpath(self.DEFAULT_CONFIG_FILE_NAME)


CONFIG = Config()
