from abc import ABC

from bisq.common.setup.log_setup import get_logger
from bisq.core.network.http.async_http_client import AsyncHttpClient

logger = get_logger(__name__)

class HttpClientProvider(ABC):
    def __init__(self, http_client: AsyncHttpClient, base_url: str, ignore_socks5_proxy=False):
        self.http_client = http_client
        logger.debug(f"{self.__class__.__name__} with baseUrl {base_url}")
        http_client.base_url = base_url
        http_client.ignore_socks5_proxy = ignore_socks5_proxy

    def __str__(self):
        return f"HttpClientProvider{{\n     httpClient={self.http_client}\n}}"
