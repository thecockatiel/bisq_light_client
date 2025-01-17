from typing import Literal
import uuid
from requests import Session, Response

import bisq.common.version as Version
from bisq.core.network.http.http_client import HttpClient
from bisq.core.network.http.http_client_utils import parse_and_validate_url
from bisq.core.network.p2p.network.socks5_proxy import Socks5Proxy
from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
from bisq.common.setup.log_setup import get_logger
from utils.time import get_time_ms

logger = get_logger(__name__)


class HttpClientImpl(HttpClient):
    uid: str

    def __init__(
        self, base_url: str = None, socks5_proxy_provider: Socks5ProxyProvider = None
    ):
        self._base_url = None
        self._base_url_host_is_onion = False
        self.socks5_proxy_provider = socks5_proxy_provider
        self.uid = str(uuid.uuid4())
        self.has_pending_request = False
        self.ignore_socks5_proxy = False
        super().__init__()
        self.session = Session()
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
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Error while closing http client session: {e}")
        finally:
            self.session = Session()

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

        socks5_proxy: Socks5Proxy = None
        proxies = None

        if not self.ignore_socks5_proxy:
            socks5_proxy = self._get_socks5_proxy()
            
        if socks5_proxy:
            proxies = {
                'http': f'socks5h://{socks5_proxy.host}:{socks5_proxy.port}',
                'https': f'socks5h://{socks5_proxy.host}:{socks5_proxy.port}',
            }

        logger.debug(
            f"_do_request: base_url={self.base_url}, url={url}, params={params}, httpMethod={http_method}, proxy={socks5_proxy}"
        )

        ts = get_time_ms()

        try:
            if self._base_url_host_is_onion:
                verify_ssl = False
            else:
                verify_ssl = True
            response: Response = self.session.request(
                http_method,
                self.base_url + url,
                data=data,
                params=params,
                headers=headers,
                allow_redirects=True,
                proxies=proxies,
                verify=verify_ssl,
            )
            self.session.cookies.clear()

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
    
    def _get_socks5_proxy(self):
        if not self.socks5_proxy_provider:
            return None

        # We use the custom socks5ProxyHttp.
        socks5_proxy = self.socks5_proxy_provider.get_socks5_proxy_http()
        if socks5_proxy:
            return socks5_proxy
        
        # If not set we request socks5_proxy_provider.get_socks5_proxy()
        # which delivers the btc proxy if set, otherwise the internal proxy.        
        return self.socks5_proxy_provider.get_socks5_proxy()

    def __str__(self):
        return f"HttpClient(socks5_proxy_provider={self.socks5_proxy_provider}, base_url='{self.base_url}', ignore_socks5_proxy={self.ignore_socks5_proxy}, uid='{self.uid}')"
