from asyncio import Future
import os
from pathlib import Path
import platform
import re
import tarfile
from typing import TYPE_CHECKING, Optional, Union
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.network.tor_mode import TorMode
from bisq.core.network.utils.utils import Utils
from utils.aio import as_future, run_in_thread
from utils.network import download_file
from utils.time import get_time_ms
from txtorcon import Tor, TorConfig, launch
from twisted.internet import reactor


if TYPE_CHECKING:
    from bisq.core.network.p2p.network.bridge_address_provider import (
        BridgeAddressProvider,
    )

logger = get_logger(__name__)

CURRENT_TOR_VERSION = "14.0.3"

class NewTor(TorMode):
    """
    This class creates a brand new instance of the Tor onion router.
    
    When asked, the class checks, whether command line parameters such as
    --torrcFile and --torrcOptions are set and if so, takes these settings into
    account. Then, a fresh set of Tor binaries is installed and Tor is launched.
    Finally, a Tor instance is returned for further use.
    """
    def __init__(
        self,
        app_data_dir: Path,
        tor_dir: Path,
        torrc_file: Optional[Path] = None,
        torrc_options: str = "",
        bridge_address_provider: "BridgeAddressProvider" = None,
        use_bridges_file=True,
    ):
        super().__init__(tor_dir)
        self.torrc_file = torrc_file
        self.torrc_options = torrc_options
        self.bridge_address_provider = bridge_address_provider
        self.use_bridges_file = use_bridges_file
        self.app_data_dir = app_data_dir

    async def get_tor(self) -> Optional["Tor"]:
        ts1 = get_time_ms()
        
        ## BEGIN PREPARE tor
        tor_bin_path = self._find_tor_in_data()
        if tor_bin_path is None:
            tor_bin_path = await self._download_and_extract_tor()
            if tor_bin_path is None:
                msg = "Failed to download and extract tor binary"
                logger.error(msg)
                raise RuntimeError(msg)
        tor_bin_dir = tor_bin_path.parent
        ## END PREPARE tor

        config_data = dict[str, Union[bool, int, str, list[str]]]()

        # check if the user wants to provide his own torrc file and update our defaults
        config_data.update(await run_in_thread(self._read_torrc_file_as_dict))

        bridge_entries = (
            self.bridge_address_provider.get_bridge_addresses()
            if self.bridge_address_provider
            else None
        )
        if bridge_entries:
            logger.info(f"Using bridges: {','.join(bridge_entries)}")
            config_data["UseBridges"] = 1
            for bridge in bridge_entries:
                self._add_line_to_config_data(f"Bridge {bridge}", config_data)
        elif self.use_bridges_file:
            lines = await run_in_thread(self._read_bridges_file)
            if lines:
                logger.info(f"Using bridges file: {','.join(lines)}")
                config_data["UseBridges"] = 1
                for line in lines:
                    self._add_line_to_config_data(f"Bridge {line}", config_data)

        # check if the user wants to temporarily add to the default torrc file
        if self.torrc_options:
            for line in self.torrc_options.split(","):
                added = self._add_line_to_config_data(line, config_data)
                if not added:
                    logger.error(
                        f"custom torrc override parse error ('{line}'). skipping..."
                    )

        config = TorConfig()
        # set defaults (some taken from torrc of bisq):
        # config.SafeSocks = 0 # unsure if this is needed.
        config.HiddenServiceStatistics = 1
        config.CookieAuthentication = 1
        config.AvoidDiskWrites = 1
        config.SOCKSPort = Utils.find_free_system_port()
        
        config.CookieAuthFile = str(self.tor_dir.joinpath('.tor', 'control_auth_cookie'))
        config.PidFile = str(self.tor_dir.joinpath('pid'))
        
        # config.Log = ["notice stdout"]
        config.DormantCanceledByStartup = 1
        config.DormantOnFirstStartup = 0
        config.ClientTransportPlugin = [
            "meek_lite,obfs2,obfs3,obfs4,scramblesuit,webtunnel exec " + 
                        str(tor_bin_dir.joinpath("pluggable_transports", "lyrebird")) +
                        ".exe\n" if platform.system().lower() == "windows" else "\n",
            "snowflake exec " + 
                        str(tor_bin_dir.joinpath("pluggable_transports", "snowflake-client")) +
                        ".exe\n" if platform.system().lower() == "windows" else "\n",
            "conjure exec " + 
                        str(tor_bin_dir.joinpath("pluggable_transports", "conjure-client")) +
                        ".exe\n" if platform.system().lower() == "windows" else "\n"
        ]
        config.GeoIPFile = str(tor_bin_dir.parent.joinpath("data", "geoip"))
        config.GeoIPv6File = str(tor_bin_dir.parent.joinpath("data", "geoip6"))
            
        
        for key, value in config_data.items():
            setattr(config, key, value)

        # write torrc for debugging purposes
        await run_in_thread(self._write_torrc_for_debugging, config)

        logger.info("Starting tor")
        result = await as_future(
            launch(reactor,
                   tor_binary=str(tor_bin_path),
                   data_directory=str(self.tor_dir),
                   progress_updates=lambda percent, tag, summary: logger.trace(f"Tor: {percent}%: {tag} - {summary}"),
                   kill_on_stderr=True,
                   _tor_config=config,
                )
        )
        logger.info(
            "\n################################################################\n"
            f"Tor started after {get_time_ms() - ts1} ms. Listening on {config.SOCKSPort[0]} Start publishing hidden service.\n"
            "################################################################"
        )

        return result

    def get_hidden_service_directory(self) -> Path:
        return self.tor_dir.joinpath(TorMode.HIDDEN_SERVICE_DIRECTORY)
    
    ################################ new code
    
    def _read_torrc_file_as_dict(self):
        """checks if user has provided torrc_file config and reads it. if not, returns empty dict"""
        config_data = dict[str, Union[bool, int, str, list[str]]]()
        if self.torrc_file:
            try:
                with open(self.torrc_file, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        self._add_line_to_config_data(line, config_data)
            except:
                logger.error(
                    f"custom torrc file not found ('{self.torrc_file}'). Proceeding with defaults."
                )
        return config_data

    def _add_line_to_config_data(
        self, line: str, config_data: dict[str, Union[bool, int, str, list[str]]]
    ):
        line = line.strip()
        if line.startswith("#") or not line:
            return False
        # split line by whitespace
        parts = line.split(None, 1)
        if len(parts) == 1 and "=" in parts[0]:
            parts = parts[0].split("=", 1)

        if len(parts) == 2:
            key, value = parts
            if key.startswith('--'):
                key = key[2:]
            if key in config_data:
                if isinstance(config_data[key], list):
                    config_data[key].append(value)
                else:
                    config_data[key] = [config_data[key], value]
            else:
                config_data[key] = value
            return True
        return False

    def _read_bridges_file(self):
        lines: list[str] = []
        try:
            with open(self.tor_dir.joinpath("bridges"), "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lines.append(line)
        except:
            logger.warning(
                f"bridges file not found ('{self.tor_dir.joinpath("bridges")}'). this is normal, continuing operation..."
            )
        return lines

    def _write_torrc_for_debugging(self, tor_config: TorConfig):
        with open(self.tor_dir.joinpath("torrc_log"), "w") as f:
            f.write(tor_config.create_torrc())

    ################################ tor download and discovery utils
    
    def _find_tor_in_data(self):
        """
        Tries to find tor binary in app's user data directory Returns None if not found.
        """
        os_name = platform.system().lower() 
        expected_bin_dir = self._tor_binaries_path.joinpath(self._get_tor_bin_dir_name(), "tor")
        
        if expected_bin_dir.exists():
            if os_name == "windows":
                path = expected_bin_dir.joinpath("tor.exe")
                if path.is_file():
                    return path
            else:
                path = expected_bin_dir.joinpath("tor")
                if path.is_file():
                    return path

        return None
    
    @property
    def _tor_binaries_path(self):
        return self.app_data_dir.joinpath("tor_binaries")
    
    async def _download_and_extract_tor(self):
        """
        Downloads tor binary and extracts it to tor_dir
        """
        tor_bin_url = self._get_tor_binary_url()
        self._tor_binaries_path.mkdir(parents=True, exist_ok=True)
        tor_bin_dir = self._tor_binaries_path.joinpath(self._get_tor_bin_dir_name())
        tor_bin_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            downloaded_file = await download_file(self.app_data_dir, tor_bin_url)
        except Exception as e:
            logger.error(f"Failed to download tor binary: {e}")
            return None
        try: 
            with tarfile.open(str(downloaded_file)) as archive:
                archive.extractall(str(tor_bin_dir))
        except:
            logger.error("Failed to extract tor binary. archive corrupted? removing the archive to download again")
            try:
                downloaded_file.unlink(True)
            except Exception as e:
                print(e)
                pass
            return None
        
        return self._find_tor_in_data()
    
    def _get_tor_bin_dir_name(self, version=CURRENT_TOR_VERSION) -> str:
        name = os.path.basename(self._get_tor_binary_url(version))
        match = re.match(r'^tor-expert-bundle-\w+-(.*)\.tar\.gz$', name)
        if match:
            return match.group(1)
        else:
            raise RuntimeError(f"Failed to extract tor path from {name}")
        
    def _get_tor_binary_url(self, version=CURRENT_TOR_VERSION):
        """returns tor binary download url based on the OS and architecture"""
        os_name = platform.system().lower()
        arch = platform.machine()
        x86_64 = ['AMD64', 'x86_64']

        if "arm" in arch:
            raise RuntimeError("ARM architecture is not supported")

        if os_name == "windows":
            if arch in x86_64:
                return f"https://archive.torproject.org/tor-package-archive/torbrowser/{version}/tor-expert-bundle-windows-x86_64-{version}.tar.gz"
            else:
                return f"https://archive.torproject.org/tor-package-archive/torbrowser/{version}/tor-expert-bundle-windows-i686-{version}.tar.gz"
        if os_name == "darwin":
            if arch == "aarch64":
                return f"https://archive.torproject.org/tor-package-archive/torbrowser/{version}/tor-expert-bundle-macos-aarch64-{version}.tar.gz"
            if arch in x86_64:
                return f"https://archive.torproject.org/tor-package-archive/torbrowser/{version}/tor-expert-bundle-macos-x86_64-{version}.tar.gz"

        if os_name == "linux":
            if arch in x86_64:
                return f"https://archive.torproject.org/tor-package-archive/torbrowser/{version}/tor-expert-bundle-linux-x86_64-{version}.tar.gz"
            else:
                return f"https://archive.torproject.org/tor-package-archive/torbrowser/{version}/tor-expert-bundle-linux-i686-{version}.tar.gz"
        
        raise RuntimeError(f"Unsupported OS: {os_name} arch: {arch}")
        