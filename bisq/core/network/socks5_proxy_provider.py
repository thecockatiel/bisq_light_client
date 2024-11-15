import socket
from typing import Optional
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.p2p.network.socks5_proxy_internal_factory import Socks5ProxyInternalFactory
from bisq.log_setup import get_logger

logger = get_logger(__name__)

def get_proxy_from_address(socks5_proxy_address: str):
    if socks5_proxy_address:
        if "socks5://" in socks5_proxy_address:
            socks5_proxy_address = socks5_proxy_address.replace("socks5://", "")
        elif "socks5h://" in socks5_proxy_address:
            socks5_proxy_address = socks5_proxy_address.replace("socks5h://", "")

        tokens = socks5_proxy_address.split(":")
        if len(tokens) == 2:
            if not tokens[1].isdigit():
                logger.error(f"Port must be a number. socks5ProxyAddress={socks5_proxy_address}")
                return None
            return Socks5Proxy(tokens[0], int(tokens[1]))
        else:
            logger.error(f"Incorrect format for socks5ProxyAddress. Should be: host:port.\nsocks5ProxyAddress={socks5_proxy_address}")
    return None

class Socks5ProxyProvider:
    """
    Unlike the original Socks5ProxyProvider in bisq, this only provides socks5 proxies for p2p network and http requests. bitcoin network is omitted from this project.
    By default there is only used the bisq internal Tor proxy, which is used for the P2P network
    If the user provides a socks5ProxyHttpAddress it will be used for http requests
    If no socks5ProxyHttpAddress is defined (default) we use the internal tor proxy.
    """
    
    def __init__(self, socks5_proxy_http_address: str = None):
        if socks5_proxy_http_address:
            self.socks5_proxy_http_address = get_proxy_from_address(socks5_proxy_http_address)
        else:
            self.socks5_proxy_http_address = None
            
        self._socks5_proxy_internal_factory: Socks5ProxyInternalFactory = None
    
    def get_socks5_proxy(self):
        if self._socks5_proxy_internal_factory:
            return self._socks5_proxy_internal_factory.get_socks5_proxy()
        return None
    
    def get_socks5_proxy_http(self):
        return self.socks5_proxy_http_address
    
    def get_socks5_proxy_internal(self):
        return self._socks5_proxy_internal_factory.get_socks5_proxy()
    
    def set_socks5_proxy_internal(self, bisq_socks5_proxy_factory: Optional[Socks5ProxyInternalFactory]):
        self._socks5_proxy_internal_factory = bisq_socks5_proxy_factory