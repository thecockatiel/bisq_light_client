from bisq.core.network.http.async_http_client_impl import AsyncHttpClientImpl 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider


class MempoolHttpClient(AsyncHttpClientImpl):

    def __init__(self, socks5_proxy_provider: "Socks5ProxyProvider" = None):
        super().__init__(socks5_proxy_provider=socks5_proxy_provider)

    # returns JSON of the transaction details
    async def get_tx_details(self, tx_id: str) -> str:
        super().shut_down()  # close any prior incomplete request
        
        api = "/" + tx_id
        return await self.get(api)

    async def request_tx_as_hex(self, tx_id: str) -> str:
        super().shut_down()  # close any prior incomplete request

        api = "/" + tx_id + "/hex"
        return await self.get(api)
