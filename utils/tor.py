import socket
from typing import Optional, Tuple
import txtorcon
import platform
import os
import re

from bisq.logging import get_logger
from utils.network import download_file 
import tarfile
from utils.dir import user_dir
from utils.aio import get_asyncio_loop

# Global variables
CURRENT_TOR_VERSION = "14.0"
tor: txtorcon.Tor = None
logger = get_logger(__name__)

async def setup_tor(reactor):
    global tor, logger
    if tor is None:
        try:
            net_addr = __detect_tor_socks_proxy()
            if net_addr:
                logger.debug(f"Tor is already running at: {net_addr[0]}:{net_addr[1]}. skipping tor launch")
                return int(net_addr[1])
        except Exception as e:
            pass
        
        tor_bin_path = __find_tor_in_data()

        if tor_bin_path is None:
            tor_bin_path = await __download_and_extract_tor()
            if tor_bin_path is None:
                raise RuntimeError("Failed to download and extract tor binary")

        tor_data_path = __create_and_get_tor_dir().joinpath("data")
        tor_data_path.mkdir(parents=True, exist_ok=True)
        tor_bin_dir = tor_bin_path.parent
        
        tor_config = txtorcon.TorConfig()
        tor_config.AvoidDiskWrites = 1
        tor_config.Log = ["notice stdout"]
        tor_config.DormantCanceledByStartup = 1
        tor_config.DormantOnFirstStartup = 0
        tor_config.ClientTransportPlugin = [
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
        tor_config.GeoIPFile = str(tor_bin_dir.parent.joinpath("data", "geoip"))
        tor_config.GeoIPv6File = str(tor_bin_dir.parent.joinpath("data", "geoip6"))

        # read "bridges" file from tor_data_path directory and add it to tor_config
        bridges_file = tor_data_path.joinpath("bridges")
        if bridges_file.exists():
            try:
                with open(bridges_file, "r") as f:
                    tor_config.UseBridges = 1
                    bridges = f.read().splitlines()
                    tor_config.Bridge = bridges
            except Exception as e:
                logger.error(f"Failed to read bridges file: {e}")


        # write config as log for debugging purposes
        with open(tor_data_path.joinpath("torrc.log"), "w") as f:
            f.write(tor_config.create_torrc())


        tor = await txtorcon.launch(reactor, 
                        progress_updates=lambda percent, tag, summary: logger.info(f"{percent}%: {tag} - {summary}"),
                        tor_binary=str(tor_bin_path),
                        data_directory=str(tor_data_path),
                        kill_on_stderr=True,
                        _tor_config=tor_config).asFuture(get_asyncio_loop())
    socks_port = await tor.protocol.get_conf("SOCKSPort").asFuture(get_asyncio_loop())
    return int(socks_port["SocksPort"])


def __is_tor_socks_port(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=10) as s:
            # mimic "tor-resolve 0.0.0.0".
            # see https://github.com/spesmilo/electrum/issues/7317#issuecomment-1369281075
            # > this is a socks5 handshake, followed by a socks RESOLVE request as defined in
            # > [tor's socks extension spec](https://github.com/torproject/torspec/blob/7116c9cdaba248aae07a3f1d0e15d9dd102f62c5/socks-extensions.txt#L63),
            # > resolving 0.0.0.0, which being an IP, tor resolves itself without needing to ask a relay.
            s.send(b'\x05\x01\x00\x05\xf0\x00\x03\x070.0.0.0\x00\x00')
            if s.recv(1024) == b'\x05\x00\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00':
                return True
    except socket.error:
        pass
    return False

def __detect_tor_socks_proxy() -> Optional[Tuple[str, int]]:
    # Probable ports for Tor to listen at
    candidates = [
        ("127.0.0.1", 9050),
        ("127.0.0.1", 9150),
    ]
    for net_addr in candidates:
        if __is_tor_socks_port(*net_addr):
            return net_addr
    return None

def __create_and_get_tor_dir():
    path = user_dir().joinpath("tor")
    path.mkdir(parents=True, exist_ok=True)
    return path

def __find_tor_in_data():
    """
    Tries to find tor binary in app's user data directory Returns None if not found.
    """
    tor_dir = __create_and_get_tor_dir()
    os_name = platform.system().lower() 
    expected_bin_dir = tor_dir.joinpath(__get_tor_bin_dir_name(), "tor")
    
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

async def __download_and_extract_tor():
    """
    Downloads tor binary and extracts it to the app's user data directory.
    """
    tor_bin_url = __get_tor_binary_url()
    tor_bin_dir = __create_and_get_tor_dir().joinpath(__get_tor_bin_dir_name())
    tor_bin_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        downloaded_file = await download_file(tor_bin_url)
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
    
    return __find_tor_in_data()

def __get_tor_binary_url(version=CURRENT_TOR_VERSION):
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

def __get_tor_bin_dir_name(version=CURRENT_TOR_VERSION) -> str:
    name = os.path.basename(__get_tor_binary_url(version))
    match = re.match(r'^tor-expert-bundle-\w+-(.*)\.tar\.gz$', name)
    if match:
        return match.group(1)
    else:
        raise RuntimeError(f"Failed to extract tor path from {name}")
