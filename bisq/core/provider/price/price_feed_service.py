from concurrent.futures import Future
from datetime import timedelta, datetime
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.common.util.math_utils import MathUtils
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.provider.price.price_request import PriceRequest
from bisq.core.provider.price.price_request_exception import PriceRequestException
from utils.data import SimpleProperty
from typing import TYPE_CHECKING, Dict, Optional, Callable
from bisq.core.provider.price.price_provider import PriceProvider
from bisq.core.monetary.price import Price
import random
from utils.time import get_time_ms
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.provider.price.market_price import MarketPrice


if TYPE_CHECKING:
    from bisq.core.provider.providers_repository import ProvidersRepository
    from bisq.core.provider.price.market_price import MarketPrice
    from bisq.core.network.http.http_client import HttpClient
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.common.handlers.fault_handler import FaultHandler
    from bisq.core.provider.price.pricenode_dto import PricenodeDto

logger = get_logger(__name__)

# TODO: implement preferences
# right now we use "USD" as preferred currency code.


class PriceFeedService:
    PERIOD_SEC = 90

    def __init__(
        self,
        http_client: "HttpClient",
        fee_service: "FeeService",
        providers_repository: "ProvidersRepository",
    ):
        self.http_client = http_client
        self.providers_repository = providers_repository
        self.fee_service = fee_service

        self.cache: dict[str, "MarketPrice"] = {}
        self.price_provider = PriceProvider(http_client, providers_repository.base_url)
        self.price_consumer: Optional[Callable[[float], None]] = None
        self.fault_handler: Optional["FaultHandler"] = None
        self.currency_code_property: SimpleProperty[Optional[str]] = SimpleProperty(
            None
        )
        self.update_counter = SimpleProperty(0)
        self.epoch_in_millis_at_last_request: int = 0
        self.retry_delay: int = 1
        self.request_ts: int = 0
        self.base_url_of_responding_provider: Optional[str] = None
        self.request_timer: Optional["Timer"] = None
        self.retry_with_new_provider_timer: Optional["Timer"] = None
        self.price_request: Optional["PriceRequest"] = None

    @property
    def currency_code(self) -> Optional[str]:
        return self.currency_code_property.get()

    @currency_code.setter
    def currency_code(self, value: Optional[str]):
        if self.currency_code_property.get() == None:
            self.currency_code_property.set(value)
            if self.price_consumer is not None:
                self.apply_price_to_consumer()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def shut_down(self) -> None:
        if self.request_timer:
            self.request_timer.stop()
            self.request_timer = None
        if self.retry_with_new_provider_timer:
            self.retry_with_new_provider_timer.stop()
            self.retry_with_new_provider_timer = None
        if self.price_request:
            self.price_request.shut_down()

    def set_currency_code_on_init(self) -> None:
        if self.currency_code is None:
            # preferred_trade_currency = self.preferences.preferred_trade_currency
            # code = preferred_trade_currency.code if preferred_trade_currency else "USD"
            code = "USD"  # Default until preferences are implemented
            self.currency_code = code

    def initial_request_price_feed(self) -> None:
        self.request(False)

    @property
    def has_prices(self) -> bool:
        return bool(self.cache)

    def request_price_feed(
        self, result_handler: Callable[[float], None], fault_handler: "FaultHandler"
    ) -> None:
        self.price_consumer = result_handler
        self.fault_handler = fault_handler
        self.request(True)

    @property
    def provider_node_address(self) -> str:
        return self.http_client.base_url

    def request(self, repeat_requests: bool) -> None:
        if self.request_ts == 0:
            logger.debug(f"request from provider {self.providers_repository.base_url}")
        else:
            logger.debug(
                f"request from provider {self.providers_repository.base_url} "
                f"{(get_time_ms() - self.request_ts) / 1000:.1f} sec. after last request"
            )

        self.request_ts = get_time_ms()
        self.base_url_of_responding_provider = None

        def on_success() -> None:
            self.base_url_of_responding_provider = self.price_provider.base_url

            # At applyPriceToConsumer we also check if price is not exceeding max. age for price data.
            success = self.apply_price_to_consumer()
            if success:
                market_price = self.cache.get(self.currency_code, None)
                if (market_price):
                    logger.debug(
                        f"Received new {market_price} from provider {self.base_url_of_responding_provider} "
                        f"after {(get_time_ms() - self.request_ts) / 1000:.1f} sec."
                    )
                else:
                    logger.debug(
                        f"Received new data from provider {self.base_url_of_responding_provider} "
                        f"after {(get_time_ms() - self.request_ts) / 1000:.1f} sec. "
                        f"Requested market price for currency {self.currency_code} was not provided. "
                        "That is expected if currency is not listed at provider."
                    )
            else:
                logger.warning(
                    "applyPriceToConsumer was not successful. We retry with a new provider."
                )
                self.retry_with_new_provider()

        def on_error(error_message: str, throwable: Exception) -> None:
            if isinstance(throwable, PriceRequestException):
                base_url_of_faulty_request = throwable.price_provider_base_url
                base_url_of_current_request = self.price_provider.base_url

                if base_url_of_current_request == base_url_of_faulty_request:
                    logger.warning(
                        f"We received an error: baseUrlOfCurrentRequest={base_url_of_current_request}, "
                        f"baseUrlOfFaultyRequest={base_url_of_faulty_request}, error={str(throwable)}"
                    )
                    self.retry_with_new_provider()
                else:
                    logger.debug(
                        "We received an error from an earlier request. We have started a new request already "
                        f"so we ignore that error. baseUrlOfCurrentRequest={base_url_of_current_request}, "
                        f"baseUrlOfFaultyRequest={base_url_of_faulty_request}"
                    )
            else:
                logger.warning(f"We received an error with throwable={str(throwable)}")
                self.retry_with_new_provider()

            if self.fault_handler:
                self.fault_handler(error_message, throwable)

        self.request_all_prices(self.price_provider, on_success, on_error)

        if repeat_requests:
            if self.request_timer:
                self.request_timer.stop()

            delay = PriceFeedService.PERIOD_SEC + random.randint(0, 4)

            def delayed_request():
                # If we have not received a result from the last request. We try a new provider.
                if self.base_url_of_responding_provider is None:
                    old_base_url = self.price_provider.base_url
                    self.set_new_price_provider()
                    logger.warning(
                        f"We did not received a response from provider {old_base_url}. "
                        f"We select the new provider {self.price_provider.base_url} and use that for a new request."
                    )
                self.request(True)

            self.request_timer = UserThread.run_after(
                delayed_request, timedelta(seconds=delay)
            )

    def retry_with_new_provider(self) -> None:
        # We increase retry delay each time until we reach PERIOD_SEC to not exceed requests.

        if self.retry_with_new_provider_timer:
            # If we have a retry timer already running we keep the old one and return.
            return

        def retry_action() -> None:
            self.retry_delay = min(self.retry_delay + 5, PriceFeedService.PERIOD_SEC)

            old_base_url = self.price_provider.base_url
            self.set_new_price_provider()
            logger.warning(
                f"We received an error at the request from provider {old_base_url}. "
                f"We select the new provider {self.price_provider.base_url} and use that for a new request. "
                f"retryDelay was {self.retry_delay} sec."
            )

            self.request(True)
            self.retry_with_new_provider_timer = None

        self.retry_with_new_provider_timer = UserThread.run_after(
            retry_action, timedelta(seconds=self.retry_delay)
        )

    def set_new_price_provider(self) -> None:
        self.providers_repository.select_next_provider_base_url()
        if self.providers_repository.base_url:
            self.price_provider = PriceProvider(
                self.http_client, self.providers_repository.base_url
            )
        else:
            logger.warning(
                "We cannot create a new priceProvider because new base url is empty."
            )

    def get_market_price(self, currency_code: str) -> Optional["MarketPrice"]:
        return self.cache.get(currency_code, None)

    def set_bisq_market_price(self, currency_code: str, price: "Price") -> None:
        if self.apply_price_to_cache(currency_code, price):
            self.update_counter.set(self.update_counter.get() + 1)

    def get_last_request_timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.epoch_in_millis_at_last_request / 1000)

    def apply_initial_bisq_market_price(self, price_by_currency_code: Dict[str, "Price"]) -> None:
        for currency_code, price in price_by_currency_code.items():
            self.apply_price_to_cache(currency_code, price)
        self.update_counter.set(self.update_counter.get() + 1)

    def apply_price_to_cache(self, currency_code: str, price: "Price") -> bool:
        if currency_code not in self.cache or not self.cache[currency_code].is_externally_provided_price:
            scale = 8 if is_crypto_currency(currency_code) else 4
            self.cache[currency_code] = MarketPrice(
                currency_code,
                MathUtils.scale_down_by_power_of_10(price.value, scale),
                0,
                False
            )
            return True
        return False

    def get_bsq_price(self) -> Optional["Price"]:
        bsq_market_price = self.get_market_price("BSQ")
        if bsq_market_price is not None:
            bsq_price_as_long = MathUtils.round_double_to_long(
                MathUtils.scale_up_by_power_of_10(
                    bsq_market_price.price,
                    Altcoin.SMALLEST_UNIT_EXPONENT
                )
            )
            return Price.value_of("BSQ", bsq_price_as_long)
        return None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private 
    # ///////////////////////////////////////////////////////////////////////////////////////////\


    def apply_price_to_consumer(self) -> bool:
        result = False
        error_message = None
        if self.currency_code is not None:
            base_url = self.price_provider.base_url
            if self.currency_code in self.cache:
                try:
                    market_price = self.cache.get(self.currency_code, None)
                    if market_price.is_externally_provided_price:
                        if market_price.is_recent_price_available:
                            if self.price_consumer is not None:
                                self.price_consumer(market_price.price)
                            result = True
                        else:
                            error_message = (
                                f"Price for currency {self.currency_code} is outdated by "
                                f"{((get_time_ms()//1000) - market_price.timestamp_sec) / 60} minutes. "
                                f"Max. allowed age of price is {MarketPrice.MARKET_PRICE_MAX_AGE_SEC / 60} minutes. "
                                f"priceProvider={base_url}. "
                                f"marketPrice={market_price}"
                            )
                    else:
                        if self.base_url_of_responding_provider is None:
                            logger.debug(
                                f"Market price for currency {self.currency_code} was not delivered by provider "
                                f"{base_url}. That is expected at startup."
                            )
                        else:
                            logger.debug(
                                f"Market price for currency {self.currency_code} is not provided by the provider "
                                f"{base_url}. That is expected for currencies not listed at providers."
                            )
                        result = True
                except Exception as e:
                    error_message = (
                        f"Exception at apply_price_to_consumer for currency {self.currency_code}. "
                        f"priceProvider={base_url}. Exception={str(e)}"
                    )
            else:
                logger.debug(
                    f"We don't have a price for currency {self.currency_code}. priceProvider={base_url}. "
                    "That is expected for currencies not listed at providers."
                )
                result = True
        else:
            error_message = "We don't have a currency yet set. That should never happen"

        if error_message is not None:
            logger.warning(error_message)
            if self.fault_handler is not None:
                self.fault_handler(error_message, PriceRequestException(error_message))

        self.update_counter.set(self.update_counter.get() + 1)
        return result

    def request_all_prices(
        self, provider: "PriceProvider", result_handler: Callable[[], None], fault_handler: "FaultHandler"
    ) -> None:
        if self.http_client.has_pending_request:
            logger.debug(
                f"We have a pending request open. This is expected when we got repeated calls. "
                f"We ignore that request. httpClient {self.http_client}"
            )
            return

        self.price_request = PriceRequest()

        def on_success(result: "PricenodeDto") -> None:
            if result is None:
                raise ValueError("result must not be None at request_all_prices")
            # Each currency rate has a different timestamp, depending on when
            # the priceNode aggregate rate was calculated
            # However, the request timestamp is when the pricenode was queried
            self.epoch_in_millis_at_last_request = get_time_ms()

            for price_data in result["data"]:
                self.cache[price_data["currencyCode"]] = MarketPrice(
                    price_data["currencyCode"],
                    price_data.price,
                    price_data["timestampSec"],
                    True
                )

            if result.bitcoin_fees_ts > 0:
                self.fee_service.update_fee_info(
                    result.bitcoin_fee_info.btc_tx_fee,
                    result.bitcoin_fee_info.btc_min_tx_fee
                )
                        
        def on_done(future: Future["PricenodeDto"]):
            try:
                result = future.result()
                UserThread.execute(lambda: on_success(result))
            except Exception as e:
                UserThread.execute(
                    lambda: fault_handler("Could not load marketPrices", e)
                )
            

        future = self.price_request.request_all_prices(provider)
        
        future.add_done_callback(on_done)
