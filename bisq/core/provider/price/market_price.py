from dataclasses import dataclass
from time import time

@dataclass
class MarketPrice:
    MARKET_PRICE_MAX_AGE_SEC = 1800  # 30 min

    currency_code: str
    price: float
    timestamp_sec: int
    is_externally_provided_price: bool

    @property
    def is_price_available(self) -> bool:
        return self.price > 0

    @property
    def is_recent_price_available(self) -> bool:
        return self.is_price_available and self.timestamp_sec > (int(time()) - MarketPrice.MARKET_PRICE_MAX_AGE_SEC)

    @property
    def is_recent_external_price_available(self) -> bool:
        return self.is_externally_provided_price and self.is_recent_price_available
