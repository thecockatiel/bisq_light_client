from collections import defaultdict
from collections.abc import Callable
import os
from pathlib import Path
import argparse
import re
import tempfile
from typing import Any, Optional
from bisq.common.config.base_currency_network import BaseCurrencyNetwork
from bisq.common.config.config_exception import ConfigException
from bisq.common.config.config_file_reader import ConfigFileReader
from electrum_min import constants as ElectrumConstants
from utils.argparse_ext import CustomArgumentParser, parse_bool
from utils.dir import user_data_dir
from utils.tor import parse_tor_hidden_service_port

def is_running_in_vscode():
    return 'VSCODE_PID' in os.environ or 'VSCODE_CWD' in os.environ

def _random_app_name():
    try:
        temp_file = tempfile.NamedTemporaryFile(
            prefix="Bisq", suffix="Temp", delete=True, delete_on_close=True
        )
        temp_file.close()
        filename = os.path.basename(temp_file.name)
        return filename
    except IOError as e:
        raise IOError(f"Failed to create temporary file: {e}")


def _temp_user_data_dir():
    return Path(tempfile.mkdtemp(prefix="BisqTempUserData"))


def _comma_separated_str_list(value: str):
    return value.split(",")


_torrc_options_re = re.compile(r"^([^\s,]+\s[^,]+,?\s*)+$")


def _parse_regex(value: re.Pattern) -> Callable[[str], str]:
    def check_regex(v: str) -> str:
        if not value.match(v):
            raise argparse.ArgumentTypeError(
                f"Value '{v}' does not match regex '{value.pattern}'"
            )
        return v

    return check_regex


def get_if_is_file_and_exists_and_is_readable_or_none(path: Path) -> Optional[Path]:
    if (
        isinstance(path, Path)
        and path.is_file()
        and path.exists()
        and os.access(path, os.R_OK)
    ):
        return path
    return None




class Config:
    # Default values for certain options
    UNSPECIFIED_PORT = -1
    DEFAULT_REGTEST_HOST = "localhost"
    DEFAULT_NUM_CONNECTIONS_FOR_BTC_PROVIDED = 7  # down from BitcoinJ default of 12
    DEFAULT_NUM_CONNECTIONS_FOR_BTC_PUBLIC = 9
    DEFAULT_FULL_DAO_NODE = False
    DEFAULT_CONFIG_FILE_NAME = "bisq.properties"

    MAX_SEQUENCE_NUMBER_MAP_SIZE_BEFORE_PURGE = 1000

    BASE_CURRENCY_NETWORK_VALUE = BaseCurrencyNetwork.BTC_MAINNET

    def __init__(
        self,
        default_app_name: Optional[str] = None,
        default_user_data_dir: Optional[Path] = None,
    ):
        # Default "data dir properties", i.e. properties that can determine the location of
        # Bisq's application data directory (appDataDir)
        if is_running_in_vscode() and (not default_app_name or not default_user_data_dir):
            default_app_name = "bisq_light_client"
            default_user_data_dir =  user_data_dir()
        self.default_app_name = default_app_name or _random_app_name()
        self.default_user_data_dir = default_user_data_dir or _temp_user_data_dir()
        self.default_app_data_dir = self.default_user_data_dir.joinpath(
            self.default_app_name
        )
        self.default_config_file = self.default_app_data_dir.joinpath(
            Config.DEFAULT_CONFIG_FILE_NAME
        )

        self.app_data_dir: Path = None  # used by self.parse_options_from

        options = defaultdict[str, Any](lambda: None)

        self.parser = self.get_config_parser()

        cli_opts = {
            key: value
            for key, value in vars(self.parser.parse_known_args()[0]).items()
            if value is not None
        }  # get only present options

        options.update(cli_opts)

        config_file: Path = None
        cli_has_config_file_opt = options["configFile"] is not None
        config_file_has_been_processed = False
        if cli_has_config_file_opt:
            config_file = Path(options["configFile"])
            if config_file.is_absolute():
                config_file_opts = self.parse_options_from(config_file)
                if config_file_opts:
                    options.update(
                        {
                            key: value
                            for key, value in vars(config_file_opts).items()
                            if value is not None
                        }  # get only present options
                    )
                    config_file_has_been_processed = True

        self.app_name: str = options["appName"] or self.default_app_name
        self.user_data_dir: Path = options["userDataDir"] or self.default_user_data_dir
        self.app_data_dir: Path = options["appDataDir"] or self.user_data_dir.joinpath(
            self.app_name
        )
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

        # If the config file has not yet been processed, either because a relative
        # path was provided at the command line, or because no value was provided at
        # the command line, attempt to process the file now, falling back to the
        # default config file location if none was specified at the command line.
        if not config_file_has_been_processed:
            config_file = (
                self.app_data_dir.joinpath(str(config_file))
                if cli_has_config_file_opt and not config_file.is_absolute()
                else self.app_data_dir.joinpath(Config.DEFAULT_CONFIG_FILE_NAME)
            )
            config_file_opts = self.parse_options_from(config_file)
            if config_file_opts:
                options.update(
                    {
                        key: value
                        for key, value in vars(config_file_opts).items()
                        if value is not None
                    }  # get only present options
                )

        # Assign all remaining properties, with command line options taking
        # precedence over those provided in the config file (if any)
        self.help_requested = options["helpRequested"] or False
        self.config_file = config_file
        self.node_port: int = options["nodePort"] or 9999
        self.max_memory: int = options["maxMemory"] or 1200
        self.log_level: str = options["logLevel"] or "INFO"
        self.banned_btc_nodes: list[str] = options["bannedBtcNodes"] or []
        self.filter_provided_btc_nodes: list[str] = (
            options["filterProvidedBtcNodes"] or []
        )
        self.banned_price_relay_nodes: list[str] = (
            options["bannedPriceRelayNodes"] or []
        )
        self.banned_seed_nodes: list[str] = options["bannedSeedNodes"] or []
        self.filter_provided_seed_nodes: list[str] = (
            options["filterProvidedSeedNodes"] or []
        )
        self.base_currency_network = BaseCurrencyNetwork[
            options["baseCurrencyNetwork"] or "BTC_MAINNET"
        ]
        self.ignore_local_btc_node: bool = options["ignoreLocalBtcNode"] or False
        self.bitcoin_regtest_host: str = options["bitcoinRegtestHost"] or ""
        self.torrc_file = get_if_is_file_and_exists_and_is_readable_or_none(
            options["torrcFile"]
        )
        self.torrc_options: str = options["torrcOptions"] or ""
        self.tor_use_bridges_file: bool = options["torUseBridgesFile"] or True
        self.tor_control_host: str = options["torControlHost"] or "127.0.0.1"
        self.tor_control_port: int = (
            options["torControlPort"] or Config.UNSPECIFIED_PORT
        )
        self.tor_control_password: str = options["torControlPassword"] or ""
        self.tor_control_cookie_file = (
            get_if_is_file_and_exists_and_is_readable_or_none(
                options["torControlCookieFile"]
            )
        )
        self.use_tor_control_safe_cookie_auth: bool = (
            options["torControlUseSafeCookieAuth"] or False
        )
        self.tor_stream_isolation: bool = options["torStreamIsolation"] or False
        self.tor_proxy_host: str = options["torProxyHost"] or ""
        self.tor_proxy_port: int = options["torProxyPort"] or Config.UNSPECIFIED_PORT
        self.tor_proxy_username: str = options["torProxyUsername"] or ""
        self.tor_proxy_password: str = options["torProxyPassword"] or ""
        self.tor_proxy_hidden_service_name: str = (
            options["torProxyHiddenServiceName"] or ""
        )
        self.tor_proxy_hidden_service_port: int = (
            options["torProxyHiddenServicePort"][0]
            if options["torProxyHiddenServicePort"]
            else Config.UNSPECIFIED_PORT
        )
        self.tor_proxy_hidden_service_target_port: int = (
            options["torProxyHiddenServicePort"][1]
            if options["torProxyHiddenServicePort"]
            else Config.UNSPECIFIED_PORT
        )
        self.referral_id: str = options["referralId"] or ""
        self.use_dev_commands: bool = options["useDevCommands"] or False
        self.use_dev_mode: bool = options["useDevMode"] or False
        self.use_dev_mode_header: bool = options["useDevModeHeader"] or False
        self.use_dev_privilege_keys: bool = options["useDevPrivilegeKeys"] or False
        self.dump_statistics: bool = options["dumpStatistics"] or False
        self.ignore_dev_msg: bool = options["ignoreDevMsg"] or False
        self.providers: list[str] = options["providers"] or []
        self.seed_nodes: list[str] = options["seedNodes"] or []
        self.ban_list: list[str] = options["banList"] or []
        self.use_localhost_for_p2p: (
            bool
        ) = not self.base_currency_network.is_mainnet() and (
            options["useLocalhostForP2P"] or False
        )
        self.max_connections: int = options["maxConnections"] or 12
        self.socks5_proxy_btc_address: str = options["socks5ProxyBtcAddress"] or ""
        self.socks5_proxy_http_address: str = options["socks5ProxyHttpAddress"] or ""
        self.msg_throttle_per_sec: int = options["msgThrottlePerSec"] or 200
        self.msg_throttle_per_10_sec: int = options["msgThrottlePer10Sec"] or 1000
        self.send_msg_throttle_trigger: int = options["sendMsgThrottleTrigger"] or 20
        self.send_msg_throttle_sleep: int = options["sendMsgThrottleSleep"] or 50
        self.btc_nodes: list[str] = options["btcNodes"] or []
        self.use_tor_for_btc: bool = options["useTorForBtc"] or False
        self.use_tor_for_btc_option_set_explicitly = options["useTorForBtc"] is not None
        self.socks5_discover_mode: str = options["socks5DiscoverMode"] or "ALL"
        self.use_all_provided_nodes: bool = options["useAllProvidedNodes"] or False
        self.user_agent: str = options["userAgent"] or "Bisq"
        self.num_connections_for_btc: int = (
            options["numConnectionsForBtc"]
            or Config.DEFAULT_NUM_CONNECTIONS_FOR_BTC_PROVIDED
        )
        self.rpc_user = options["rpcUser"] or ""
        self.rpc_password = options["rpcPassword"] or ""
        self.rpc_host = options["rpcHost"] or ""
        self.rpc_port = options["rpcPort"] or Config.UNSPECIFIED_PORT
        self.rpc_block_notification_port = (
            options["rpcBlockNotificationPort"] or Config.UNSPECIFIED_PORT
        )
        self.rpc_block_notification_host = options["rpcBlockNotificationHost"] or ""
        self.dump_blockchain_data: bool = options["dumpBlockchainData"] or False
        self.full_dao_node: bool = (
            options["fullDaoNode"] or Config.DEFAULT_FULL_DAO_NODE
        )
        self.full_dao_node_option_set_explicitly: bool = (
            options["fullDaoNode"] is not None
        )
        self.genesis_tx_id: str = options["genesisTxId"] or ""
        self.genesis_block_height: int = options["genesisBlockHeight"] or -1
        self.genesis_total_supply: int = options["genesisTotalSupply"] or -1
        self.dump_delayed_payout_txs: bool = options["dumpDelayedPayoutTxs"] or False
        self.allow_faulty_delayed_txs: bool = options["allowFaultyDelayedTxs"] or False
        self.api_password: str = options["apiPassword"] or ""
        self.api_port: int = options["apiPort"] or 9998
        self.prevent_periodic_shutdown_at_seed_node: bool = (
            options["preventPeriodicShutdownAtSeedNode"] or False
        )
        self.republish_mailbox_entries: bool = (
            options["republishMailboxEntries"] or False
        )
        self.bypass_mempool_validation: bool = (
            options["bypassMempoolValidation"] or False
        )
        self.dao_node_api_url: str = options["daoNodeApiUrl"] or "http://localhost"
        self.dao_node_api_port: int = options["daoNodeApiPort"] or 8081
        self.is_bm_full_node: bool = options["isBmFullNode"] or False
        self.bm_oracle_node_pub_key: str = options["bmOracleNodePubKey"] or ""
        self.bm_oracle_node_priv_key: str = options["bmOracleNodePrivKey"] or ""
        self.seed_node_reporting_server_url: str = (
            options["seedNodeReportingServerUrl"] or ""
        )
        self.use_full_mode_dao_monitor: bool = (
            options["useFullModeDaoMonitor"] or False
        )
        self.use_full_mode_dao_monitor_option_set_explicitly: bool = (
            options["useFullModeDaoMonitor"] is not None
        )

        # Create all appDataDir subdirectories and assign to their respective properties
        btc_network_dir = self.app_data_dir.joinpath(
            self.base_currency_network.name.lower()
        )
        btc_network_dir.mkdir(parents=True, exist_ok=True)

        self.key_storage_dir = btc_network_dir.joinpath("keys")
        self.key_storage_dir.mkdir(parents=True, exist_ok=True)

        self.storage_dir = btc_network_dir.joinpath("db")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.tor_dir = btc_network_dir.joinpath("tor")
        self.tor_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        self.wallet_dir = btc_network_dir.joinpath("electrum_wallet")
        self.wallet_dir.mkdir(parents=True, exist_ok=True)

        # Assign values to special-case static fields
        Config.BASE_CURRENCY_NETWORK_VALUE = self.base_currency_network

        # set electrum to use the same network parameters as the base currency network
        if self.base_currency_network.is_regtest():
            ElectrumConstants.set_regtest()
        elif self.base_currency_network.is_testnet():
            ElectrumConstants.set_testnet()

    @property
    def network_parameters(self):
        return self.base_currency_network.parameters

    @property
    def base_currency_network_parameters(self):
        return self.base_currency_network.parameters

    def parse_options_from(self, config_file: Path) -> Optional[argparse.Namespace]:
        if not config_file.exists():
            if self.app_data_dir and config_file != self.app_data_dir.joinpath(
                Config.DEFAULT_CONFIG_FILE_NAME
            ):
                raise ConfigException(
                    f"The specified config file '{config_file}' does not exist."
                )
            return None

        config_file_reader = ConfigFileReader(config_file)
        option_lines = ["--" + line for line in config_file_reader.get_option_lines()]

        parsed_config = self.parser.parse_known_args(option_lines)[0]

        for arg in ["helpRequested", "configFile"]:
            if getattr(parsed_config, arg):
                if (
                    arg == "configFile"
                    and getattr(parsed_config, arg) == Config.DEFAULT_CONFIG_FILE_NAME
                ):
                    continue
                raise ConfigException(
                    f"Option '{arg}' is not allowed in the config file."
                )

        return parsed_config

    def get_config_parser(self) -> CustomArgumentParser:
        parser = CustomArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            allow_abbrev=False,
            add_help=False,
        )
        parser.add_argument(
            "-h",
            "--help",
            dest="helpRequested",
            help=(
                "Print this help text." 
            ),
            action="store_true",
        )
        parser.add_argument(
            "--configFile",
            help=(
                f"Specify configuration file. "
                f"Relative paths will be prefixed by appDataDir location."
            ),
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--appName",
            help="Application name",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--userDataDir",
            help="User data directory",
            type=Path,
            metavar="<File>",
        )
        parser.add_argument(
            "--appDataDir",
            help="Application data directory",
            type=Path,
            metavar="<File>",
        )
        parser.add_conditional_argument(
            "--nodePort",
            help="Port to listen on",
            type=int,
            metavar="<Integer>",
            unavailable_if=["torProxyHiddenServicePort"],
        )
        parser.add_argument(
            "--maxMemory",
            help="Max. permitted memory (used only by headless versions)",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--logLevel",
            help="Set logging level",
            type=str,
            metavar="<OFF|ALL|ERROR|WARN|INFO|DEBUG|TRACE>",
            choices=["OFF", "ALL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"],
        )
        parser.add_argument(
            "--bannedBtcNodes",
            help="List Bitcoin nodes to ban",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--filterProvidedBtcNodes",
            help="List of filter provided Bitcoin nodes",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--bannedPriceRelayNodes",
            help="List Bisq price nodes to ban",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--bannedSeedNodes",
            help="List Bisq seed nodes to ban",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--filterProvidedSeedNodes",
            help="List of filter provided seed nodes",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--baseCurrencyNetwork",
            help="Base currency network",
            type=str,
            metavar="<BTC_MAINNET|BTC_TESTNET|BTC_REGTEST|BTC_DAO_TESTNET|BTC_DAO_BETANET|BTC_DAO_REGTEST>",
            choices=[
                "BTC_MAINNET",
                "BTC_TESTNET",
                "BTC_REGTEST",
                "BTC_DAO_TESTNET",
                "BTC_DAO_BETANET",
                "BTC_DAO_REGTEST",
            ],
        )
        parser.add_argument(
            "--ignoreLocalBtcNode",
            help="If set to true a Bitcoin Core node running locally will be ignored",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--bitcoinRegtestHost",
            help="Bitcoin Core node when using BTC_REGTEST network",
            type=str,
            metavar="<host[:port]>",
        )
        parser.add_argument(
            "--referralId",
            help="Optional Referral ID (e.g. for API users or pro market makers)",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--useDevCommands",
            help="Enables dev commands which is used for convenience for developer testing",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--useDevMode",
            help="Enables dev mode which is used for convenience for developer testing",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--useDevModeHeader",
            help="Use dev mode css scheme to distinguish dev instances.",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--useDevPrivilegeKeys",
            help="If set to true all privileged features requiring a private key to be enabled are overridden by a dev key pair (This is for developers only!)",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--dumpStatistics",
            help="If set to true dump trade statistics to a json file in appDataDir",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--ignoreDevMsg",
            help=(
                "If set to true all signed network_messages "
                "from bisq developers are ignored (Global alert, "
                "Version update alert, Filters for offers, nodes or "
                "trading account data)"
            ),
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--providers",
            help="List custom pricenodes",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--seedNodes",
            help=(
                "Override hard coded seed nodes as comma separated list e.g. "
                "'rxdkppp3vicnbgqt.onion:8002,mfla72c4igh5ta2t.onion:8002'"
            ),
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--banList",
            help="Nodes to exclude from network connections.",
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--useLocalhostForP2P",
            help="Use localhost P2P network for development. Only available for non-BTC_MAINNET configuration.",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--maxConnections",
            help="Max. connections a peer will try to keep",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--socks5ProxyBtcAddress",
            help="A proxy address to be used for Bitcoin network.",
            type=str,
            metavar="<host:port>",
        )
        parser.add_argument(
            "--socks5ProxyHttpAddress",
            help="A proxy address to be used for Http requests (should be non-Tor)",
            type=str,
            metavar="<host:port>",
        )
        parser.add_conditional_argument(
            "--torrcFile",
            help=(
                "An existing torrc-file to be sourced for Tor. Note that torrc-entries, "
                "which are critical to Bisq's correct operation, cannot be overwritten."
            ),
            type=Path,
            metavar="<File>",
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torrcOptions",
            help=(
                "A list of torrc-entries to amend to Bisq's torrc. Note that "
                "torrc-entries, which are critical to Bisq's flawless operation, cannot be overwritten. "
                "[torrc options line, torrc option, ...]"
            ),
            type=_parse_regex(_torrc_options_re),
            metavar="<String>",
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torUseBridgesFile",
            help="Use lines from 'bridges' file in Tor data directory as bridge entries, if exists. Defaults to True.",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torControlHost",
            help="The control hostname of an already running Tor service to be used by Bisq.",
            type=str,
            metavar="<String>",
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torControlPort",
            help="The control port of an already running Tor service to be used by Bisq.",
            type=int,
            metavar="<port>",
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torControlPassword",
            help="The password for controlling the already running Tor service.",
            type=str,
            metavar="<String>",
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torControlCookieFile",
            help=(
                "The cookie file for authenticating against the already "
                "running Tor service. Use in conjunction with --torControlUseSafeCookieAuth"
            ),
            type=Path,
            metavar="<File>",
            unavailable_if=[
                "torProxyHost",
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_argument(
            "--torControlUseSafeCookieAuth",
            help="Use the SafeCookie method when authenticating to the already running Tor service.",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_disabled_argument(
            "--torStreamIsolation",
            help="This option is not supported. Do NOT use.",
            disable_message="torStreamIsolation is not supported. Do NOT use.",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_conditional_argument(
            "--torProxyHost",
            help="The proxy hostname of an already running Tor service to be used by Bisq.",
            type=str,
            metavar="<String>",
            unavailable_if=["torControlHost", "torControlPort", "torControlPassword"],
            needs=[
                "torProxyPort",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torProxyPort",
            help="The proxy port of an already running Tor service to be used by Bisq.",
            type=int,
            metavar="<port>",
            unavailable_if=["torControlHost", "torControlPort", "torControlPassword"],
            needs=[
                "torProxyHost",
                "torProxyHiddenServiceName",
                "torProxyHiddenServicePort",
            ],
        )
        parser.add_conditional_argument(
            "--torProxyUsername",
            help="The proxy username of an already running Tor service to be used by Bisq.",
            type=str,
            metavar="<String>",
            available_if=["torProxyPort", "torProxyHost"],
            unavailable_if=["torControlHost", "torControlPort", "torControlPassword"],
        )
        parser.add_conditional_argument(
            "--torProxyPassword",
            help="The proxy password of an already running Tor service to be used by Bisq.",
            type=str,
            metavar="<String>",
            available_if=["torProxyPort", "torProxyHost"],
            unavailable_if=["torControlHost", "torControlPort", "torControlPassword"],
        )
        parser.add_conditional_argument(
            "--torProxyHiddenServiceName",
            help="The published hidden service hostname of an already running Tor service to be used by Bisq.",
            type=str,
            metavar="<String>",
            unavailable_if=["torControlHost", "torControlPort", "torControlPassword"],
            needs=["torProxyHost", "torProxyPort", "torProxyHiddenServicePort"],
        )
        parser.add_conditional_argument(
            "--torProxyHiddenServicePort",
            help="The hidden service port of an already running Tor service to be used by Bisq. This is the same syntax as the 'HiddenServicePort' option of Tor, but does not support unix paths and can only be passed once.",
            type=parse_tor_hidden_service_port,
            metavar="<VIRTPORT [TARGET[:PORT]]>",
            unavailable_if=["torControlHost", "torControlPort", "torControlPassword"],
            needs=["torProxyHost", "torProxyPort", "torProxyHiddenServiceName"],
        )
        parser.add_argument(
            "--msgThrottlePerSec",
            help="Message throttle per sec for connection class",
            type=int,
            metavar="<Integer>",
            # With PERMITTED_MESSAGE_SIZE of 200kb results in bandwidth of 40MB/sec or 5 mbit/sec
        )
        parser.add_argument(
            "--msgThrottlePer10Sec",
            help="Message throttle per 10 sec for connection class",
            type=int,
            metavar="<Integer>",
            # With PERMITTED_MESSAGE_SIZE of 200kb results in bandwidth of 20MB/sec or 2.5 mbit/sec
        )
        parser.add_argument(
            "--sendMsgThrottleTrigger",
            help="Time in ms when we trigger a sleep if 2 messages are sent",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--sendMsgThrottleSleep",
            help="Pause in ms to sleep if we get too many messages to send",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--btcNodes",
            help=(
                "Override provided Bitcoin nodes as comma separated list e.g. "
                "'rxdkppp3vicnbgqt.onion:8002,mfla72c4igh5ta2t.onion:8002'"
            ),
            type=_comma_separated_str_list,
            metavar="<host:port[,...]>",
        )
        parser.add_argument(
            "--useTorForBtc",
            help="If set to true BitcoinJ is routed over tor (socks 5 proxy).",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--socks5DiscoverMode",
            help="Specify discovery mode for Bitcoin nodes. One or more of: [ADDR, DNS, ONION, ALL] (comma separated, they get OR'd together)",
            type=str,
            metavar="<mode[,...]>",
        )
        parser.add_argument(
            "--useAllProvidedNodes",
            help="Set to true if connection of bitcoin nodes should include clear net nodes",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--userAgent",
            help="User agent at btc node connections",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--numConnectionsForBtc",
            help="Number of connections to the Bitcoin network",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--rpcUser",
            help="Bitcoind rpc username",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--rpcPassword",
            help="Bitcoind rpc password",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--rpcHost",
            help="Bitcoind rpc host",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--rpcPort",
            help="Bitcoind rpc port",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--rpcBlockNotificationPort",
            help="Bitcoind rpc port for block notifications",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--rpcBlockNotificationHost",
            help="Bitcoind rpc accepted incoming host for block notifications",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--dumpBlockchainData",
            help="If set to true the blockchain data from RPC requests to Bitcoin Core are stored as json file in the data dir.",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--fullDaoNode",
            help=(
                "If set to true the node requests the blockchain data via RPC requests "
                "from Bitcoin Core and provide the validated BSQ txs to the network. It requires that the "
                "other RPC properties are set as well."
            ),
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--genesisTxId",
            help="Genesis transaction ID when not using the hard coded one",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--genesisBlockHeight",
            help="Genesis transaction block height when not using the hard coded one",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--genesisTotalSupply",
            help="Genesis total supply when not using the hard coded one",
            type=int,
            metavar="<Integer>",
        )
        parser.add_argument(
            "--dumpDelayedPayoutTxs",
            help="Dump delayed payout transactions to file",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--allowFaultyDelayedTxs",
            help="Allow completion of trades with faulty delayed payout transactions",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--apiPassword",
            help="gRPC API password",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--apiPort",
            help="gRPC API port",
            type=int,
        )
        parser.add_argument(
            "--preventPeriodicShutdownAtSeedNode",
            help="Prevents periodic shutdown at seed nodes",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--republishMailboxEntries",
            help="Republish mailbox messages at startup",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--bypassMempoolValidation",
            help="Prevents mempool check of trade parameters",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--daoNodeApiUrl",
            help="Dao node API url",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--daoNodeApiPort",
            help="Dao node API port",
            type=int,
        )
        parser.add_argument(
            "--isBmFullNode",
            help="Run as Burningman full node",
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        parser.add_argument(
            "--bmOracleNodePubKey",
            help="Burningman oracle node public key",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--bmOracleNodePrivKey",
            help="Burningman oracle node private key",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--seedNodeReportingServerUrl",
            help="URL of seed node reporting server",
            type=str,
            metavar="<String>",
        )
        parser.add_argument(
            "--useFullModeDaoMonitor",
            help=(
                "If set to true full mode DAO monitor is activated. "
                "By that at each block during parsing the dao state hash is created, "
                "otherwise only after block parsing is complete and on new blocks."
            ),
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        return parser
