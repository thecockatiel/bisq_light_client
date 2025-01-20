from functools import total_ordering
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.locale.currency_util import get_crypto_currency, get_fiat_currency
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
import proto.pb_pb2 as protobuf
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.monetary.volume import Volume
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
from bisq.core.network.p2p.storage.payload.data_sorted_truncatable_payload import (
    DateSortedTruncatablePayload,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.trade.statistics.trade_statistics_3_payment_method_wrapper import TradeStatistics3PaymentMethodWrapper
from bisq.core.util.json_util import JsonUtil
from utils.java_compat import java_arrays_byte_hashcode, java_string_hashcode, long_unsigned_right_shift


if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade



logger = get_logger(__name__)


@total_ordering
class TradeStatistics3(
    DateSortedTruncatablePayload,
    PersistableNetworkPayload,
    CapabilityRequiringPayload,
    ProcessOncePersistableNetworkPayload,
):
    """
    This new trade statistics class uses only the bare minimum of data.
    Data size is about 50 bytes in average
    """

    STRICT_FILTER_DATE = int(
        datetime(2021, 11, 1, tzinfo=timezone.utc).timestamp() * 1000
    )

    def __init__(
        self,
        currency: str,
        price: int,
        amount: int,
        payment_method: str,
        date: int,
        mediator: Optional[str] = None,
        refund_agent: Optional[str] = None,
        extra_data_map: Optional[dict[str, str]] = None,
        hash: Optional[bytes] = None,
    ):
        super().__init__()
        self.currency = currency
        self.price = price
        self.amount = amount
        temp_payment_method = None
        try:
            temp_payment_method = str(TradeStatistics3PaymentMethodWrapper[payment_method].value)
        except:
            temp_payment_method = payment_method
        self.payment_method = temp_payment_method
        self.date = date
        self.mediator = mediator
        self.refund_agent = refund_agent
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(extra_data_map)
        if not hash:
            self.hash = self.create_hash()
        else:
            self.hash = hash
            
        self._date_obj = datetime.fromtimestamp(self.date / 1000, tz=timezone.utc) # transient
        self._price_obj: Price = None # transient
        self._volume: Volume = None # Fiat or altcoin volume # transient
        
    def create_hash(self) -> bytes:
        # We create hash from all fields excluding hash itself. We use json as simple data serialisation.
        # TradeDate is different for both peers so we ignore it for hash. ExtraDataMap is ignored as well as at
        # software updates we might have different entries which would cause a different hash.
        return get_sha256_ripemd160_hash(JsonUtil.object_to_json(self).encode('utf-8'))
    
    # to manually handle names of expected json and also to handle the transient fields from java
    def get_json_dict(self) -> dict:
        return {
            "currency": self.currency,
            "price": self.price,
            "amount": self.amount,
            "paymentMethod": self.payment_method,
            "date": self.date,
        }

    def to_proto_trade_statistics_3(self):
        builder = protobuf.TradeStatistics3(
            currency=self.currency,
            price=self.price,
            amount=self.amount,
            payment_method=self.payment_method,
            date=self.date,
            hash=self.hash,
        )
        if self.mediator:
            builder.mediator = self.mediator
        if self.refund_agent:
            builder.refund_agent = self.refund_agent
        if self.extra_data_map:
            builder.extra_data.update(self.extra_data_map)
        return builder
    
    def to_proto_message(self):
        return protobuf.PersistableNetworkPayload(
            trade_statistics3=self.to_proto_trade_statistics_3()
        )
    
    @staticmethod
    def from_proto(proto: protobuf.TradeStatistics3):
        return TradeStatistics3(
            currency=proto.currency,
            price=proto.price,
            amount=proto.amount,
            payment_method=proto.payment_method,
            date=proto.date,
            mediator=ProtoUtil.string_or_none_from_proto(proto.mediator),
            refund_agent=ProtoUtil.string_or_none_from_proto(proto.refund_agent),
            extra_data_map=dict(proto.extra_data) if proto.extra_data else None,
            hash=proto.hash,
        )
        
    @staticmethod
    def from_trade(trade: "Trade", referral_id: Optional[str], is_tor_network_node: bool):
        extra_data_map = dict[str, str]()
        if not referral_id:
            extra_data_map[OfferPayload.REFERRAL_ID] = referral_id
        
        assert trade.mediator_node_address is not None
        mediator_node_address = trade.mediator_node_address
        # The first 4 chars are sufficient to identify a mediator.
        # For testing with regtest/localhost we use the full address as its localhost and would result in
        # same values for multiple mediators.
        truncated_mediator_address = mediator_node_address.get_full_address()[:4] if is_tor_network_node else mediator_node_address.get_full_address()
        
        # RefundAgentNodeAddress can be None if converted from old version.
        truncated_refund_agent_address = None
        refund_agent_node_address = trade.refund_agent_node_address
        if refund_agent_node_address:
            truncated_refund_agent_address = refund_agent_node_address.get_full_address()[:4] if is_tor_network_node else refund_agent_node_address.get_full_address()
        
        assert trade.get_offer() is not None
        offer = trade.get_offer()
        return TradeStatistics3(
            currency=offer.currency_code,
            price=trade.get_price().value,
            amount=trade.get_amount_as_long(),
            payment_method=offer.payment_method.id,
            date=int(trade.get_date().timestamp() * 1000),
            mediator=truncated_mediator_address,
            refund_agent=truncated_refund_agent_address,
            extra_data_map=extra_data_map,
        )
    
    @staticmethod
    def from_bsq_swap_trade(bsq_swap_trade: "BsqSwapTrade"):
        assert bsq_swap_trade.get_offer() is not None
        offer = bsq_swap_trade.get_offer()
        return TradeStatistics3(
            currency=offer.currency_code,
            price=bsq_swap_trade.get_price().value,
            amount=bsq_swap_trade.get_amount_as_long(),
            payment_method=offer.payment_method.id,
            date=bsq_swap_trade.take_offer_date,
        )
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_hash(self):
        return self.hash
    
    def verify_hash_size(self):
        assert self.hash is not None, "hash must not be None"
        return len(self.hash) == 20
    
    def get_required_capabilities(self):
        return Capabilities(Capability.TRADE_STATISTICS_3)

    def get_date(self):
        return self._date_obj

    def max_items(self):
        return 15000
    
    def prune_optional_data(self):
        self.mediator = None
        self.refund_agent = None
    
    def get_payment_method_id(self):
        if not self.payment_method or self.payment_method[0] > '9':
            return self.payment_method    
        try: 
            return TradeStatistics3PaymentMethodWrapper(int(self.payment_method)).name
        except:
            return self.payment_method

    def get_trade_price(self):
        if not self._price_obj:
            self._price_obj = Price.value_of(self.currency, self.price)
        return self._price_obj

    def get_trade_amount(self):
        return Coin.value_of(self.amount)
    
    def get_trade_volume(self):
        if not self._volume:
            price = self.get_trade_price()
            if isinstance(price.monetary, Altcoin):
                self._volume = price.get_volume_by_amount(self.get_trade_amount())
            else:
                self._volume = VolumeUtil.get_rounded_fiat_volume(price.get_volume_by_amount(self.get_trade_amount()))
        return self._volume

    def is_valid(self):
        if not self.currency:
            return False
        
        valid_max_trade_limit = True
        currency_found = True
        # We had historically higher trade limits and assets which are not in the currency list anymore, so we apply
        # the filter only for data after STRICT_FILTER_DATE.
        if self.date > TradeStatistics3.STRICT_FILTER_DATE:
            max_trade_limit = Coin.COIN().multiply(2).value
            try:
                # We cover only active payment methods. Retired ones will not be found by getActivePaymentMethodById.
                payment_method_id = self.get_payment_method_id()
                payment_method = PaymentMethod.get_active_payment_method(payment_method_id)
                if payment_method:
                    max_trade_limit = payment_method.get_max_trade_limit_as_coin(self.currency).value
            except Exception as e:
                logger.warning("Error at is_valid().", exc_info=e)
            valid_max_trade_limit = self.amount <= max_trade_limit

            currency_found = (get_crypto_currency(self.currency) is not None or 
                             get_fiat_currency(self.currency) is not None)

        return (self.amount > 0 and
                valid_max_trade_limit and
                self.price > 0 and
                self.date > 0 and
                self.payment_method and
                self.currency and
                currency_found)
    
    def __lt__(self, other):
        # TODO: check if it's equivalent to java's sorting exactly
        if not isinstance(other, TradeStatistics3):
            return NotImplemented
            
        if self.date != other.date:
            return self.date < other.date
        if self.amount != other.amount:
            return self.amount < other.amount
        if self.currency != other.currency:
            if not self.currency:
                return True
            if not other.currency:
                return False
            return self.currency < other.currency
        if self.price != other.price:
            return self.price < other.price
        if self.payment_method != other.payment_method:
            if not self.payment_method:
                return True
            if not other.payment_method:
                return False
            return self.payment_method < other.payment_method
        return self.hash < other.hash
    
    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, TradeStatistics3):
            return False
        return (self.price == other.price and
            self.amount == other.amount and 
            self.date == other.date and
            self.currency == other.currency and
            self.payment_method == other.payment_method and
            self.hash == other.hash)
        
    def __hash__(self):
        result = java_string_hashcode(self.currency) if self.currency else 0
        result = 31 * result + (self.price ^ long_unsigned_right_shift(self.price, 32))
        result = 31 * result + (self.amount ^ long_unsigned_right_shift(self.amount, 32))
        result = 31 * result + (java_string_hashcode(self.payment_method) if self.payment_method else 0)
        result = 31 * result + (self.date ^ long_unsigned_right_shift(self.date, 32))
        result = 31 * result + java_arrays_byte_hashcode(self.hash)
        return result

    def __str__(self):
        return (f"TradeStatistics3{{\n"
                f"     currency='{self.currency}',\n"
                f"     price={self.price},\n"
                f"     amount={self.amount},\n"
                f"     paymentMethod='{self.payment_method}',\n"
                f"     date={self.date},\n"
                f"     mediator='{self.mediator}',\n"
                f"     refundAgent='{self.refund_agent}',\n"
                f"     hash={bytes_as_hex_string(self.hash)},\n"
                f"     extraDataMap={self.extra_data_map}\n"
                f"}}")
