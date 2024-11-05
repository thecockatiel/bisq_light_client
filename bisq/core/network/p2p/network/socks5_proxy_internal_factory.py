from abc import ABC, abstractmethod

from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy

class Socks5ProxyInternalFactory(ABC):
    
    @abstractmethod
    def get_socks5_proxy() -> Socks5Proxy:
        pass