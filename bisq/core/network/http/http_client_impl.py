from typing import Literal
import httpx
import uuid
from httpx_socks import SyncProxyTransport

import bisq.core.common.version as Version
from bisq.core.network.http.http_client import HttpClient
from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
from bisq.core.common.setup.log_setup import get_logger
from utils.time import get_time_ms

logger = get_logger(__name__)


class HttpClientImpl(HttpClient):
    uid: str

    def __init__(
        self, base_url: str = None, socks5_proxy_provider: Socks5ProxyProvider = None
    ):
        self.base_url = base_url
        self.socks5_proxy_provider = socks5_proxy_provider
        self.uid = str(uuid.uuid4())
        self.has_pending_request = False
        self.ignore_socks5_proxy = False
        self._client = None
        super().__init__()

    def shut_down(self):
        try:
            if self._client:
                self._client.close()
        except:
            pass

    def get(
        self,
        url: str,
        params: dict[str, str] = {},
        headers: dict[str, str] = {"User-Agent": f"bisq/{Version.VERSION}"},
    ):
        return self._do_request("GET", url, params=params, headers=headers)

    def post(
        self,
        url: str,
        data: dict[str, str] = None,
        params: dict[str, str] = {},
        headers: dict[str, str] = {"User-Agent": f"bisq/{Version.VERSION}"},
    ):
        return self._do_request("POST", url, data, params=params, headers=headers)

    def _do_request(
        self,
        http_method: Literal["GET"] | Literal["POST"],
        url: str,
        data: dict[str, str] = None,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
    ):
        if not self.base_url:
            raise ValueError("baseUrl must be set before calling doRequest")
        if self.has_pending_request:
            raise ValueError(
                "We got called on the same HttpClient again while a request is still open."
            )
        self.has_pending_request = True

        socks5_proxy = None

        if not self.ignore_socks5_proxy:
            socks5_proxy = self._get_socks5_proxy()

        logger.debug(
            f"_do_request: base_url={self.base_url}, url={url}, params={params}, httpMethod={http_method}, proxy={socks5_proxy}"
        )

        ts = get_time_ms()

        try:
            transport: SyncProxyTransport = None
            if socks5_proxy:
                transport = SyncProxyTransport.from_url(
                    socks5_proxy.url,
                    verify=False if ".onion" in self.base_url else True,
                )

            with httpx.Client(
                base_url=self.base_url,
                transport=transport,
                timeout=httpx.Timeout(connect=120, read=120, write=None, pool=None),
            ) as client:
                self._client = client
                response = client.request(
                    http_method,
                    url,
                    data=data,
                    params=params,
                    headers=headers,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    raise Exception(
                        f"Received errorMsg '{response.text}' with responseCode {response.status_code} from {self.base_url} {url}. Response took: {get_time_ms() - ts} ms. params: {params}"
                    )

                response = response.text

                logger.debug(
                    f"Response from {self.base_url} {url} took {(get_time_ms() - ts)} ms. Data size:{len(response)}, response: {response}, param: {params}"
                )

                return response
        finally:
            self.has_pending_request = False
            self._client = None

    def _get_socks5_proxy(self):
        if not self.socks5_proxy_provider:
            return None

        socks5_proxy = self.socks5_proxy_provider.get_socks5_proxy_http()
        if not socks5_proxy:
            socks5_proxy = self.socks5_proxy_provider.get_socks5_proxy()

        return socks5_proxy

    def __str__(self):
        return f"HttpClient(socks5_proxy_provider={self.socks5_proxy_provider}, base_url='{self.base_url}', ignore_socks5_proxy={self.ignore_socks5_proxy}, uid='{self.uid}')"
