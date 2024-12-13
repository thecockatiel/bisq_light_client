from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from typing import List, Dict, Optional

class MutableOfferPayloadFields:
    """The set of editable OfferPayload fields."""

    def __init__(self, 
                 offer_payload: OfferPayload = None,
                 fixed_price: int = 0,
                 market_price_margin: float = 0.0,
                 use_market_based_price: bool = False,
                 base_currency_code: str = "",
                 counter_currency_code: str = "",
                 payment_method_id: str = "",
                 maker_payment_account_id: str = "",
                 max_trade_limit: int = 0,
                 max_trade_period: int = 0,
                 country_code: Optional[str] = None,
                 accepted_country_codes: Optional[List[str]] = None,
                 bank_id: Optional[str] = None,
                 accepted_bank_ids: Optional[List[str]] = None,
                 extra_data_map: Optional[Dict[str, str]] = None):
        
        if offer_payload:
            self.fixed_price = offer_payload.price  # Must be 0 when market_price_margin = True (on server)
            self.market_price_margin = offer_payload.market_price_margin
            self.use_market_based_price = offer_payload.use_market_based_price
            self.base_currency_code = offer_payload.base_currency_code
            self.counter_currency_code = offer_payload.counter_currency_code
            self.payment_method_id = offer_payload.payment_method_id
            self.maker_payment_account_id = offer_payload.maker_payment_account_id
            self.max_trade_limit = offer_payload.max_trade_limit
            self.max_trade_period = offer_payload.max_trade_period
            self.country_code = offer_payload.country_code
            self.accepted_country_codes = offer_payload.accepted_country_codes
            self.bank_id = offer_payload.bank_id
            self.accepted_bank_ids = offer_payload.accepted_bank_ids
            self.extra_data_map = offer_payload.extra_data_map
        else:
            self.fixed_price = fixed_price   # Must be 0 when market_price_margin = True (on server)
            self.market_price_margin = market_price_margin
            self.use_market_based_price = use_market_based_price
            self.base_currency_code = base_currency_code
            self.counter_currency_code = counter_currency_code
            self.payment_method_id = payment_method_id
            self.maker_payment_account_id = maker_payment_account_id
            self.max_trade_limit = max_trade_limit
            self.max_trade_period = max_trade_period
            self.country_code = country_code
            self.accepted_country_codes = accepted_country_codes
            self.bank_id = bank_id
            self.accepted_bank_ids = accepted_bank_ids
            self.extra_data_map = extra_data_map

    def __str__(self) -> str:
        return (f"MutableOfferPayloadFields{{\n"
                f"  fixed_price={self.fixed_price}\n"
                f"  market_price_margin={self.market_price_margin}\n"
                f"  use_market_based_price={self.use_market_based_price}\n"
                f"  base_currency_code='{self.base_currency_code}'\n"
                f"  counter_currency_code='{self.counter_currency_code}'\n"
                f"  payment_method_id='{self.payment_method_id}'\n"
                f"  maker_payment_account_id='{self.maker_payment_account_id}'\n"
                f"  max_trade_limit='{self.max_trade_limit}'\n"
                f"  max_trade_period='{self.max_trade_period}'\n"
                f"  country_code='{self.country_code}'\n"
                f"  accepted_country_codes={self.accepted_country_codes}\n"
                f"  bank_id='{self.bank_id}'\n"
                f"  accepted_bank_ids={self.accepted_bank_ids}\n"
                f"  extra_data_map={self.extra_data_map}\n"
                "}")
