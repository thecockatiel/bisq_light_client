from bisq.core.network.http.http_client import HttpClient
from bisq.core.network.p2p.p2p_service import P2PService
from bisq.core.provider.http_client_provider import HttpClientProvider
import bisq.common.version as Version
import json

from bisq.core.provider.price.pricenode_dto import PricenodeDto


class PriceProvider(HttpClientProvider):
    def __init__(self, http_client: HttpClient, base_url: str):
        super().__init__(http_client, base_url, False)
        self.shut_down_requested = False

    def get_all(self) -> "PricenodeDto":
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
        if P2PService.get_my_node_address() is not None:
            host_name = P2PService.get_my_node_address().host_name
            hs_version = ", HSv3" if len(host_name) > 22 else ", HSv2"

        user_agent = f"bisq/{Version.VERSION}{hs_version}"
        json_response = self.http_client.get(
            "/getAllMarketPrices", headers={"User-Agent": user_agent}
        )

        return json.loads(json_response)
    
    @property
    def base_url(self):
        return self.http_client.base_url

    def shut_down(self):
        self.shut_down_requested = True
        self.http_client.shut_down()
