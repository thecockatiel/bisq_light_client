from asyncio import Future
from typing import TYPE_CHECKING, Optional
import random
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.provider.mempool_http_client import MempoolHttpClient
from utils.aio import FutureCallback, as_future


if TYPE_CHECKING:
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.shared.preferences.preferences import Preferences


class MempoolRequest:

    def __init__(self, preferences: "Preferences", socks5_proxy_provider: "Socks5ProxyProvider"):
        self.logger = get_ctx_logger(__name__)
        self.tx_broadcast_services: list[str] = preferences.get_default_tx_broadcast_services()
        self.mempool_http_client = MempoolHttpClient(socks5_proxy_provider)

    def get_tx_status(self, mempool_service_callback: Future[str], tx_id: str):
        self.mempool_http_client.base_url = self.get_random_service_address(self.tx_broadcast_services)

        def on_success(result: str): 
            self.logger.info(f"Received mempoolData of [{result}] from provider")
            mempool_service_callback.set_result(result)
         
        def on_failure(e):
            try:
                mempool_service_callback.set_exception(e)
            except:
                pass
        
        as_future(
            self.mempool_http_client.get_tx_details(tx_id)
        ).add_done_callback(
            FutureCallback(on_success, on_failure)
        )
    
    def request_tx_as_hex(self, tx_id: str) -> Future[str]:
        self.mempool_http_client.base_url = self.get_random_service_address(self.tx_broadcast_services)
        return as_future(self.mempool_http_client.request_tx_as_hex(tx_id))
    
    def switch_to_another_provider(self):
        try:
            self.tx_broadcast_services.remove(self.mempool_http_client.base_url)
        except:
            pass
        return len(self.tx_broadcast_services) > 0
        
    @staticmethod
    def get_random_service_address(tx_broadcast_services: list[str]) -> Optional[str]:
        assert tx_broadcast_services is not None, "tx_broadcast_services must not be None"
        return random.choice(tx_broadcast_services) if tx_broadcast_services else None
        