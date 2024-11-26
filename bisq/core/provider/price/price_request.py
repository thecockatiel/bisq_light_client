from concurrent.futures import CancelledError, ThreadPoolExecutor, Future
from typing import TYPE_CHECKING, Optional

from bisq.core.provider.price.price_request_exception import PriceRequestException

if TYPE_CHECKING:
    from bisq.core.provider.price.pricenode_dto import PricenodeDto
    from bisq.core.provider.price.price_provider import PriceProvider

# TODO: replace thread pool executor and shutdown flow 
class PriceRequest:
    def __init__(self):
        self.executor = ThreadPoolExecutor(
            max_workers=5,
            thread_name_prefix="PriceRequest",
        )
        self.provider: Optional["PriceProvider"] = None
        self.shut_down_requested = False

    def request_all_prices(self, provider: "PriceProvider") -> Future:
        self.provider = provider
        base_url = provider.base_url
        # NOTE: dangling future if shutdown requested?
        result_future = Future()

        def callback(future: Future["PricenodeDto"]):
            if not self.shut_down_requested:
                try:
                    result = future.result()
                    result_future.set_result(result)
                except CancelledError:
                    result_future.cancel()
                except Exception as e:
                    result_future.set_exception(PriceRequestException(e, base_url))

        future = self.executor.submit(provider.get_all)
        future.add_done_callback(callback)
        return result_future

    def shut_down(self):
        self.shut_down_requested = True
        if self.provider is not None:
            self.provider.shut_down()
        self.executor.shutdown(wait=True, cancel_futures=True)
