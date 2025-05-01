from asyncio import CancelledError, Future
from typing import TYPE_CHECKING, Optional
from utils.aio import FutureCallback, as_future

from bisq.core.provider.price.price_request_exception import PriceRequestException

if TYPE_CHECKING:
    from bisq.core.provider.price.pricenode_dto import PricenodeDto
    from bisq.core.provider.price.price_provider import PriceProvider

# TODO: replace thread pool executor and shutdown flow
class PriceRequest:
    def __init__(self):
        self.provider: Optional["PriceProvider"] = None
        self.shut_down_requested = False
        self.request_future: Optional[Future] = None

    def request_all_prices(self, provider: "PriceProvider") -> Future["PricenodeDto"]:
        self.provider = provider
        base_url = provider.base_url
        result_future = Future()

        self.request_future = future = as_future(provider.get_all())
        future.add_done_callback(
            FutureCallback(
                result_future.set_result,
                lambda e: result_future.set_exception(
                    PriceRequestException(e, base_url)
                ),
                lambda e: result_future.cancel(str(e)),
            )
        )
        return result_future

    def shut_down(self):
        self.shut_down_requested = True
        if self.provider is not None:
            self.provider.shut_down()
            self.provider = None
        if self.request_future:
            self.request_future.cancel()
            self.request_future = None
