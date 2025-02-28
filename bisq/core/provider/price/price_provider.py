import json
from typing import TYPE_CHECKING
from bisq.core.network.http.async_http_client import AsyncHttpClient
from bisq.core.provider.http_client_provider import HttpClientProvider
from bisq.common.version import Version
from bisq.core.provider.price.pricenode_dto import PricenodeDto

if TYPE_CHECKING:
    from bisq.core.network.p2p.p2p_service import P2PService

class PriceProvider(HttpClientProvider):
    def __init__(self, http_client: AsyncHttpClient, p2p_service: "P2PService", base_url: str):
        super().__init__(http_client, base_url, False)
        self._p2p_service = p2p_service
        self.shut_down_requested = False

    async def get_all(self) -> "PricenodeDto":
        if self.shut_down_requested:
            return {
                "data": [],
                "bitcoinFeesTs": 0,
                "bitcoinFeeInfo": {
                    "btcTxFee": 0,
                    "btcMinTxFee": 0,
                }
            }

        hs_version = ""
        if self._p2p_service.address is not None:
            host_name = self._p2p_service.address
            hs_version = ", HSv3" if len(host_name) > 22 else ", HSv2"

        user_agent = f"bisq/{Version.VERSION}{hs_version}"
        json_response = await self.http_client.get(
            "/getAllMarketPrices", headers={"User-Agent": user_agent}
        )

        return json.loads(json_response)
    
    @property
    def base_url(self):
        return self.http_client.base_url

    def shut_down(self):
        self.shut_down_requested = True
        self.http_client.shut_down()
