from bisq.common.setup.log_setup import get_ctx_logger
from typing import Optional
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.p2p.network.socks5_proxy_internal_factory import (
    Socks5ProxyInternalFactory,
)
class Socks5ProxyProvider:
    """
    By default there is only used the bisq internal Tor proxy, which is used for the P2P network
    If the user provides a socks5_proxy_http_address it will be used for http requests
    If the user provides a socks5_proxy_btc_address, this will be used for the btc network.
    If no socks5_proxy_http_address and no socks5_proxy_btc_address is defined (default) we use get_socks5_proxy_internal.
    """

    def __init__(
        self,
        socks5_proxy_btc_address: str = None,
        socks5_proxy_http_address: str = None,
    ):
        self.logger = get_ctx_logger(__name__)
        # proxy used for btc network
        self.socks5_proxy_btc = self.get_proxy_from_address(socks5_proxy_btc_address)

        # if defined proxy used for http requests
        self.socks5_proxy_http = self.get_proxy_from_address(socks5_proxy_http_address)

        self._socks5_proxy_internal_factory: Socks5ProxyInternalFactory = None

    def get_socks5_proxy(self):
        if self.socks5_proxy_btc:
            return self.socks5_proxy_btc
        elif self._socks5_proxy_internal_factory:
            return self._socks5_proxy_internal_factory.get_socks_proxy()
        else:
            return None

    def get_socks5_proxy_btc(self):
        return self.socks5_proxy_btc

    def get_socks5_proxy_http(self):
        return self.socks5_proxy_http

    def get_socks5_proxy_internal(self):
        return self._socks5_proxy_internal_factory.get_socks_proxy()

    def set_socks5_proxy_internal(
        self, bisq_socks5_proxy_factory: Optional[Socks5ProxyInternalFactory]
    ):
        self._socks5_proxy_internal_factory = bisq_socks5_proxy_factory

    def get_proxy_from_address(self, socks5_proxy_address: str) -> Optional[Socks5Proxy]:
        if socks5_proxy_address:
            proxy = Socks5Proxy("", 0)
            if "socks5://" in socks5_proxy_address:
                socks5_proxy_address = socks5_proxy_address.replace("socks5://", "")
            elif "socks5h://" in socks5_proxy_address:
                socks5_proxy_address = socks5_proxy_address.replace("socks5h://", "")

            if "@" in socks5_proxy_address:
                tokens = socks5_proxy_address.split("@", 1)
                if len(tokens) == 2:
                    if ":" in tokens[0]:
                        user_pass_tokens = tokens[0].split(":", 1)
                        if len(user_pass_tokens) == 2:
                            proxy.username = user_pass_tokens[0]
                            proxy.password = user_pass_tokens[1]
                        else:
                            self.logger.error(
                                f"Incorrect format for socks5_proxy_address. Should be: username:password@host:port.\nsocks5_proxy_address={socks5_proxy_address}"
                            )
                            return None
                    socks5_proxy_address = tokens[1]
                else:
                    self.logger.error(
                        f"Incorrect format for socks5_proxy_address. Should be: username:password@host:port.\nnsocks5_proxy_address={socks5_proxy_address}"
                    )
                    return None

            tokens = socks5_proxy_address.split(":")
            if len(tokens) == 2:
                if not tokens[1].isdigit():
                    self.logger.error(
                        f"Port must be a number. socks5_proxy_address={socks5_proxy_address}"
                    )
                    return None
                proxy.host = tokens[0]
                proxy.port = int(tokens[1])
                return proxy
                # NOTE: in java implementation it instantly tests the connection to the proxy, should we also do it?
            else:
                self.logger.error(
                    f"Incorrect format for socks5_proxy_address. Should be: host:port.\nsocks5_proxy_address={socks5_proxy_address}"
                )
        return None
