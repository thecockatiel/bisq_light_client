import asyncio
from typing import Literal
import uuid
import aiohttp
from aiohttp_socks import ProxyType, ProxyConnector

import bisq.common.version as Version
from bisq.core.network.http.async_http_client import AsyncHttpClient
from bisq.core.network.http.http_client_utils import parse_and_validate_url
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
from bisq.common.setup.log_setup import get_logger
from utils.time import get_time_ms

logger = get_logger(__name__)


class AsyncHttpClientImpl(AsyncHttpClient):
    uid: str

    def __init__(
        self,
        base_url: str = None,
        socks5_proxy_provider: Socks5ProxyProvider = None,
        timeout: asyncio.TimeoutError = None,
    ):
        super().__init__()
        self._base_url = None
        self._base_url_host_is_onion = False
        self.socks5_proxy_provider = socks5_proxy_provider
        self.uid = str(uuid.uuid4())
        self.has_pending_request = False
        self.ignore_socks5_proxy = False
        self.current_task: "asyncio.Task[str]" = None
        self.default_timeout = timeout
        self.base_url = base_url

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        if isinstance(value, str) and not value.startswith("http") and ".onion" in value:
            value = f"http://{value}"
        parsed = parse_and_validate_url(value)
        if parsed:
            self._base_url = value.rstrip('/')
            self._base_url_host_is_onion = parsed.hostname.endswith(".onion")
            if parsed.scheme == "http" and (parsed.hostname == "localhost" or parsed.hostname.endswith(".local")):
                self.ignore_socks5_proxy = True
            else:
                self.ignore_socks5_proxy = False
        else:
            self._base_url = None
            self._base_url_host_is_onion = False
            self.ignore_socks5_proxy = False

    def shut_down(self):
        if self.current_task:
            self.current_task.cancel()
            self.current_task = None

    def get(
        self,
        url: str,
        params: dict[str, str] = {},
        headers: dict[str, str] = {"User-Agent": f"bisq/{Version.VERSION}"},
        timeout: asyncio.TimeoutError = None,
    ):
        self.current_task = asyncio.create_task(
            self._do_request(
                "GET", url, params=params, headers=headers, timeout=timeout
            )
        )
        return self.current_task

    def post(
        self,
        url: str,
        data: dict[str, str] = None,
        params: dict[str, str] = {},
        headers: dict[str, str] = {"User-Agent": f"bisq/{Version.VERSION}"},
        timeout: asyncio.TimeoutError = None,
    ):
        self.current_task = asyncio.create_task(
            self._do_request(
                "POST", url, data, params=params, headers=headers, timeout=timeout
            )
        )
        return self.current_task

    async def _do_request(
        self,
        http_method: Literal["GET"] | Literal["POST"],
        url: str,
        data: dict[str, str] = None,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        timeout: asyncio.TimeoutError = None,
    ):
        if not self.base_url:
            raise ValueError("baseUrl must be set before calling doRequest")
        if self.has_pending_request:
            raise ValueError(
                "We got called on the same HttpClient again while a request is still open."
            )
        self.has_pending_request = True

        socks5_proxy: Socks5Proxy = None
        proxy_connector = None

        if not self.ignore_socks5_proxy:
            socks5_proxy = self._get_socks5_proxy()

        if socks5_proxy:
            if self._base_url_host_is_onion:
                verify_ssl = False
            else:
                verify_ssl = True
            proxy_connector = ProxyConnector(
                proxy_type=ProxyType.SOCKS5,
                host=socks5_proxy.host,
                port=socks5_proxy.port,
                username=socks5_proxy.username,
                password=socks5_proxy.password,
                rdns=True,
                ssl=verify_ssl,
            )
            client_timeout = (
                timeout
                or self.default_timeout
                or aiohttp.ClientTimeout(
                    sock_connect=240,
                    sock_read=240,
                )
            )
        else:
            client_timeout = (
                timeout
                or self.default_timeout
                or aiohttp.ClientTimeout(
                    sock_connect=120,
                    sock_read=120,
                )
            )

        logger.debug(
            f"_do_request: base_url={self.base_url}, url={url}, params={params}, httpMethod={http_method}, proxy={socks5_proxy}"
        )

        ts = get_time_ms()

        try:
            async with aiohttp.ClientSession(
                base_url=self.base_url,
                connector=proxy_connector,
                timeout=client_timeout,
            ) as session:
                async with session.request(
                    http_method,
                    url,
                    params=params,
                    data=data,
                    headers=headers,
                    allow_redirects=True,
                ) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Received errorMsg '{response.text}' with responseCode {response.status} from {self.base_url} {url}. Response took: {get_time_ms() - ts} ms. params: {params}"
                        )

                    response = await response.text()

                    logger.debug(
                        f"Response from {self.base_url} {url} took {(get_time_ms() - ts)} ms. Data size:{len(response)}, response: {response}, param: {params}"
                    )

                    return response
        finally:
            self.has_pending_request = False

    def _get_socks5_proxy(self):
        if not self.socks5_proxy_provider:
            return None

        # We use the custom socks5ProxyHttp.
        socks5_proxy = self.socks5_proxy_provider.get_socks5_proxy_http()
        if not socks5_proxy:
            return socks5_proxy

        # If not set we request socks5_proxy_provider.get_socks5_proxy()
        # which delivers the btc proxy if set, otherwise the internal proxy.
        return self.socks5_proxy_provider.get_socks5_proxy()

    def __str__(self):
        return f"AsyncHttpClient(socks5_proxy_provider={self.socks5_proxy_provider}, base_url='{self.base_url}', ignore_socks5_proxy={self.ignore_socks5_proxy}, uid='{self.uid}')"
