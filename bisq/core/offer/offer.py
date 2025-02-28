from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast, Any
from decimal import Decimal

from utils.preconditions import check_argument
from bisq.core.offer.bsq_swap.bsq_swap_offer_payload import BsqSwapOfferPayload
import pb_pb2 as protobuf

from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.exceptions.trade_price_out_of_tolerance_exception import TradePriceOutOfToleranceException
from bisq.core.locale.currency_util import is_crypto_currency, is_fiat_currency
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.offer.bisq_v1.market_price_not_available_exception import MarketPriceNotAvailableException
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.offer.offer_state import OfferState
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from utils.data import SimpleProperty
from bisq.core.offer.availability.offer_availability_protocol import OfferAvailabilityProtocol
from bisq.core.monetary.volume import Volume
from utils.formatting import get_short_id

if TYPE_CHECKING:
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.common.handlers.result_handler import ResultHandler
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.offer.availability.offer_availability_model import OfferAvailabilityModel
    from bisq.core.offer.offer_payload_base import OfferPayloadBase
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    
logger = get_logger(__name__)

# TODO: get_json_dict
class Offer(NetworkPayload, PersistablePayload):
    # We allow max. 1 % difference between own offerPayload price calculation and takers calculation.
    # Market price might be different at maker's and takers side so we need a bit of tolerance.
    # The tolerance will get smaller once we have multiple price feeds avoiding fast price fluctuations
    # from one provider.
    PRICE_TOLERANCE = 0.01

    def __init__(self, offer_payload_base: 'OfferPayloadBase'):
        self.offer_payload_base = offer_payload_base
        
        self.state_property = SimpleProperty(OfferState.UNKNOWN) # JsonExclude
        self.availability_protocol: Optional['OfferAvailabilityProtocol'] = None # JsonExclude
        self.error_message_property: SimpleProperty[Optional[str]] = SimpleProperty() # JsonExclude
        self.price_feed_service: Optional['PriceFeedService'] = None # JsonExclude
        
        # Used only as cache
        self._currency_code: Optional[str] = None # JsonExclude
        
    def get_json_dict(self):
        return {
            "offerPayloadBase": self.offer_payload_base,
        }

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> 'protobuf.Offer':
        if self.is_bsq_swap_offer:
            return protobuf.Offer(
                bsq_swap_offer_payload=self.offer_payload_base.to_proto_message().bsq_swap_offer_payload
            )
        else:
            assert isinstance(self.offer_payload_base, OfferPayload)
            return protobuf.Offer(
                offer_payload=self.offer_payload_base.to_proto_message().offer_payload
            )

    @staticmethod
    def from_proto(proto: 'protobuf.Offer') -> 'Offer':
        if proto.HasField('offer_payload'):
            return Offer(OfferPayload.from_proto(proto.offer_payload))
        else:
            return Offer(BsqSwapOfferPayload.from_proto(proto.bsq_swap_offer_payload))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Availability
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def check_offer_availability(self, 
                               model: 'OfferAvailabilityModel',
                               result_handler: 'ResultHandler',
                               error_message_handler: 'ErrorMessageHandler') -> None:
        self.availability_protocol = OfferAvailabilityProtocol(
            model,
            lambda: self._handle_availability_success(result_handler),
            lambda error_message: self._handle_availability_error(error_message, error_message_handler)
        )
        self.availability_protocol.send_offer_availability_request()

    def _handle_availability_success(self, result_handler: 'ResultHandler') -> None:
        self.cancel_availability_request()
        result_handler()

    def _handle_availability_error(self, error_message: str, error_message_handler: 'ErrorMessageHandler') -> None:
        self.cancel_availability_request()
        logger.error(error_message)
        error_message_handler(error_message)

    def cancel_availability_request(self) -> None:
        if self.availability_protocol is not None:
            self.availability_protocol.cancel()

    def get_price(self) -> Optional[Price]:
        currency_code = self.currency_code
        offer_payload = self.offer_payload
        
        if offer_payload is None:
            return Price.value_of(currency_code, self.offer_payload_base.price)
        
        if not offer_payload.use_market_based_price:
            return Price.value_of(currency_code, self.offer_payload_base.price)
        
        if self.price_feed_service is None:
            raise ValueError("price_feed_service must not be None")
            
        market_price = self.price_feed_service.get_market_price(currency_code)
        if market_price is not None and market_price.is_recent_external_price_available:
            market_price_margin = offer_payload.market_price_margin
            
            if is_crypto_currency(currency_code):
                factor = 1 - market_price_margin if self.direction == OfferDirection.SELL else 1 + market_price_margin
            else:
                factor = 1 - market_price_margin if self.direction == OfferDirection.BUY else 1 + market_price_margin
            
            market_price_as_double = market_price.price
            target_price_as_double = market_price_as_double * factor
            
            try:
                precision = (Altcoin.SMALLEST_UNIT_EXPONENT 
                           if is_crypto_currency(currency_code)
                           else Fiat.SMALLEST_UNIT_EXPONENT)
                
                scaled = MathUtils.scale_up_by_power_of_10(target_price_as_double, precision)
                rounded_to_long = MathUtils.round_double_to_long(scaled)
                return Price.value_of(currency_code, rounded_to_long)
            except Exception as e:
                logger.error(f"Exception at getPrice / parseToFiat: {e}\nThis case should never happen.")
                return None
        else:
            logger.trace("We don't have a market price. This case could only happen if you don't have a price feed.")
            return None

    @property
    def fixed_price(self) -> int:
        return self.offer_payload_base.price

    def verify_takers_trade_price(self, takers_trade_price: int) -> None:
        if not self.is_use_market_based_price:
            check_argument(
                takers_trade_price == self.fixed_price,
                f"Takers price does not match offer price. "
                f"Takers price={takers_trade_price}; offer price={self.fixed_price}"
            )
            return

        trade_price = Price.value_of(self.currency_code, takers_trade_price)
        offer_price = self.get_price()
        if offer_price is None:
            raise MarketPriceNotAvailableException(
                "Market price required for calculating trade price is not available."
            )

        check_argument(takers_trade_price > 0, "takers_trade_price must be positive")

        relation = Decimal(takers_trade_price) / Decimal(offer_price.get_value())
        # We allow max. 2 % difference between own offerPayload price calculation and takers calculation.
        # Market price might be different at maker's and takers side so we need a bit of tolerance.
        # The tolerance will get smaller once we have multiple price feeds avoiding fast price fluctuations
        # from one provider.
        
        deviation = abs(1 - float(relation))
        logger.info(
            f"Price at take-offer time: id={self.short_id}, "
            f"currency={self.currency_code}, "
            f"takersPrice={takers_trade_price}, "
            f"makersPrice={offer_price.get_value()}, "
            f"deviation={deviation * 100}%"
        )
        
        if deviation > self.PRICE_TOLERANCE:
            msg = (
                f"Taker's trade price is too far away from our calculated price based on the market price.\n"
                f"takersPrice={trade_price.get_value()}\n"
                f"makersPrice={offer_price.get_value()}"
            )
            logger.warning(msg)
            raise TradePriceOutOfToleranceException(msg)

    def get_volume_by_amount(self, amount: "Coin") -> Optional[Volume]:
        price = self.get_price()
        if price is None or amount is None:
            return None
            
        volume_by_amount = price.get_volume_by_amount(amount)
        if self.offer_payload_base.payment_method_id == PaymentMethod.HAL_CASH_ID:
            volume_by_amount = VolumeUtil.get_adjusted_volume_for_hal_cash(volume_by_amount)
        elif self.is_fiat_offer:
            volume_by_amount = VolumeUtil.get_rounded_fiat_volume(volume_by_amount)

        return volume_by_amount

    def reset_state(self) -> None:
        self.state = OfferState.UNKNOWN

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getter
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def offer_payload(self) -> Optional['OfferPayload']:
        if isinstance(self.offer_payload_base, OfferPayload):
            return self.offer_payload_base
        return None
    
    @property
    def tx_fee(self) -> Coin:
        if self.offer_payload:
            return Coin.value_of(self.offer_payload.tx_fee)
        return Coin.ZERO()

    @property
    def maker_fee(self) -> Coin:
        if self.offer_payload:
            return Coin.value_of(self.offer_payload.maker_fee)
        return Coin.ZERO()

    @property
    def is_currency_for_maker_fee_btc(self) -> bool:
        if self.offer_payload:
            return self.offer_payload.is_currency_for_maker_fee_btc
        return False

    @property
    def buyer_security_deposit(self) -> Coin:
        if self.offer_payload:
            return Coin.value_of(self.offer_payload.buyer_security_deposit)
        return Coin.ZERO()

    @property
    def seller_security_deposit(self) -> Coin:
        if self.offer_payload:
            return Coin.value_of(self.offer_payload.seller_security_deposit)
        return Coin.ZERO()

    @property
    def max_trade_limit(self) -> Coin:
        if self.offer_payload:
            return Coin.value_of(self.offer_payload.max_trade_limit)
        return Coin.ZERO()

    @property
    def amount(self) -> Coin:
        return Coin.value_of(self.offer_payload_base.amount)

    @property
    def min_amount(self) -> Coin:
        return Coin.value_of(self.offer_payload_base.min_amount)

    @property
    def is_range(self) -> bool:
        return self.offer_payload_base.amount != self.offer_payload_base.min_amount

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.offer_payload_base.date / 1000)  # Convert Java milliseconds to Python seconds

    @property
    def payment_method(self) -> PaymentMethod:
        return PaymentMethod.get_payment_method(self.offer_payload_base.payment_method_id)

    @property
    def short_id(self):
        return get_short_id(self.offer_payload_base.id)

    @property
    def volume(self):
        return self.get_volume_by_amount(self.amount)

    @property
    def min_volume(self):
        return self.get_volume_by_amount(self.min_amount)

    @property
    def is_buy_offer(self) -> bool:
        return self.direction == OfferDirection.BUY

    @property
    def mirrored_direction(self) -> OfferDirection:
        return OfferDirection.SELL if self.direction == OfferDirection.BUY else OfferDirection.BUY

    def is_my_offer(self, key_ring: 'KeyRing') -> bool:
        return self.pub_key_ring == key_ring.pub_key_ring

    @property
    def account_age_witness_hash_as_hex(self) -> Optional[str]:
        extra_data_map = self.extra_data_map
        if extra_data_map and OfferPayload.ACCOUNT_AGE_WITNESS_HASH in extra_data_map:
            return extra_data_map[OfferPayload.ACCOUNT_AGE_WITNESS_HASH]
        return None

    @property
    def f2f_city(self) -> str:
        if self.extra_data_map and OfferPayload.F2F_CITY in self.extra_data_map:
            return self.extra_data_map[OfferPayload.F2F_CITY]
        return ""

    @property
    def extra_info(self) -> str:
        if not self.extra_data_map:
            return ""
        if OfferPayload.F2F_EXTRA_INFO in self.extra_data_map:
            return self.extra_data_map[OfferPayload.F2F_EXTRA_INFO]
        if OfferPayload.CASH_BY_MAIL_EXTRA_INFO in self.extra_data_map:
            return self.extra_data_map[OfferPayload.CASH_BY_MAIL_EXTRA_INFO]
        return ""

    @property
    def payment_method_name_with_country_code(self) -> str:
        method = self.payment_method.get_short_name()
        method_country_code = self.country_code
        if method_country_code:
            method = f"{method} ({method_country_code})"
        return method

    @property
    def state(self) -> 'OfferState':
        return self.state_property.get()
    
    @state.setter
    def state(self, state: 'OfferState'):
        self.state_property.set(state)

    @property
    def error_message(self) -> str:
        return self.error_message_property.get()
    
    @error_message.setter
    def error_message(self, error_message: str):
        self.error_message_property.set(error_message)
        
        
    def set_offer_fee_payment_tx_id(self, offer_fee_payment_tx_id: str) -> None:
        if self.offer_payload:
            self.offer_payload.offer_fee_payment_tx_id = offer_fee_payment_tx_id

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delegate Getter
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def direction(self) -> OfferDirection:
        return self.offer_payload_base.direction

    @property
    def id(self) -> str:
        return self.offer_payload_base.id

    @property
    def accepted_bank_ids(self) -> Optional[list[str]]:
        return self.offer_payload.accepted_bank_ids if self.offer_payload else None

    @property
    def bank_id(self) -> Optional[str]:
        return self.offer_payload.bank_id if self.offer_payload else None

    @property
    def accepted_country_codes(self) -> Optional[list[str]]:
        return self.offer_payload.accepted_country_codes if self.offer_payload else None

    @property
    def country_code(self) -> Optional[str]:
        return self.offer_payload.country_code if self.offer_payload else None

    @property
    def currency_code(self) -> str:
        if self._currency_code is not None:
            return self._currency_code

        self._currency_code = (self.counter_currency_code 
                             if self.base_currency_code == "BTC" 
                             else self.base_currency_code)
        return self._currency_code

    @property
    def counter_currency_code(self) -> str:
        return self.offer_payload_base.counter_currency_code

    @property
    def base_currency_code(self) -> str:
        return self.offer_payload_base.base_currency_code

    @property
    def payment_method_id(self) -> str:
        return self.offer_payload_base.payment_method_id

    @property
    def protocol_version(self) -> int:
        return self.offer_payload_base.protocol_version

    @property
    def is_use_market_based_price(self) -> bool:
        return self.offer_payload.use_market_based_price if self.offer_payload else False

    @property
    def market_price_margin(self) -> float:
        return self.offer_payload.market_price_margin if self.offer_payload else 0.0

    @property
    def maker_node_address(self) -> 'NodeAddress':
        return self.offer_payload_base.owner_node_address

    @property
    def pub_key_ring(self) -> 'PubKeyRing':
        return self.offer_payload_base.pub_key_ring

    @property
    def maker_payment_account_id(self) -> str:
        return self.offer_payload_base.maker_payment_account_id

    @property
    def offer_fee_payment_tx_id(self) -> Optional[str]:
        return self.offer_payload.offer_fee_payment_tx_id if self.offer_payload else None

    @property
    def version_nr(self) -> str:
        return self.offer_payload_base.version_nr

    @property
    def max_trade_period(self) -> int:
        return self.offer_payload.max_trade_period if self.offer_payload else 0

    @property
    def owner_node_address(self) -> 'NodeAddress':
        return self.offer_payload_base.owner_node_address

    @property
    def owner_pub_key(self):
        return self.offer_payload_base.get_owner_pub_key()

    @property
    def extra_data_map(self) -> Optional[dict[str, str]]:
        return self.offer_payload_base.extra_data_map

    @property
    def use_auto_close(self) -> bool:
        return self.offer_payload.use_auto_close if self.offer_payload else False

    @property
    def use_re_open_after_auto_close(self) -> bool:
        return self.offer_payload.use_re_open_after_auto_close if self.offer_payload else False

    @property
    def is_bsq_swap_offer(self) -> bool:
        return isinstance(self.offer_payload_base, BsqSwapOfferPayload)

    @property
    def is_xmr_auto_conf(self) -> bool:
        if not self.is_xmr:
            return False
        if (not self.extra_data_map or 
            OfferPayload.XMR_AUTO_CONF not in self.extra_data_map):
            return False
        return self.extra_data_map[OfferPayload.XMR_AUTO_CONF] == OfferPayload.XMR_AUTO_CONF_ENABLED_VALUE

    @property
    def is_xmr(self) -> bool:
        return self.currency_code == "XMR"

    @property
    def is_fiat_offer(self) -> bool:
        return is_fiat_currency(self.currency_code)

    @property
    def bsq_swap_offer_payload(self) -> Optional['BsqSwapOfferPayload']:
        if isinstance(self.offer_payload_base, 'BsqSwapOfferPayload'):
            return self.offer_payload_base
        return None

    @property
    def offer_payload_hash(self) -> bytes:
        return self.offer_payload_base.get_hash()

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        if not isinstance(other, Offer):
            return False

        if ((self.offer_payload_base is not None and self.offer_payload_base != other.offer_payload_base) or
            (self.offer_payload_base is None and other.offer_payload_base is not None)):
            return False
        
        if self.state != other.state:
            return False
            
        return ((self.error_message is None and other.error_message is None) or
                (self.error_message is not None and self.error_message == other.error_message))

    def __hash__(self) -> int:
        result = hash(self.offer_payload_base) if self.offer_payload_base is not None else 0
        result = 31 * result + hash(self.state if self.state is not None else 0)
        result = 31 * result + hash(self.error_message if self.error_message is not None else 0)
        return result

    def __str__(self) -> str:
        return (f"Offer{{error_message='{self.error_message}', "
                f"state={self.state}, "
                f"offer_payload_base={self.offer_payload_base}}}")




