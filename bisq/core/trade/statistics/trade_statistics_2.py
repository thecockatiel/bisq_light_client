from functools import total_ordering
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
import proto.pb_pb2 as protobuf
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.core.network.p2p.storage.payload.capability_requiring_payload import (
    CapabilityRequiringPayload,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.util.json_util import JsonUtil

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade


logger = get_logger(__name__)


@total_ordering
class TradeStatistics2(
    ProcessOncePersistableNetworkPayload,
    PersistableNetworkPayload,
    CapabilityRequiringPayload,
):
    MEDIATOR_ADDRESS = "medAddr"
    REFUND_AGENT_ADDRESS = "refAddr"

    def __init__(
        self,
        direction: OfferDirection,
        base_currency: str,
        counter_currency: str,
        offer_payment_method: str,
        offer_date: int,
        offer_use_market_based_price: bool,
        offer_market_price_margin: float,
        offer_amount: int,
        offer_min_amount: int,
        offer_id: str,
        trade_price: int,
        trade_amount: int,
        trade_date: int,
        deposit_tx_id: Optional[str] = None,
        hash_bytes: Optional[bytes] = None,
        extra_data_map: Optional[dict] = None,
    ):
        self.direction = direction
        self.base_currency = base_currency
        self.counter_currency = counter_currency
        self.offer_payment_method = offer_payment_method
        self.offer_date = offer_date
        self.offer_use_market_based_price = offer_use_market_based_price
        self.offer_market_price_margin = float(
            offer_market_price_margin
        )  # this is to ensure correct json serialization
        self.offer_amount = offer_amount
        self.offer_min_amount = offer_min_amount
        self.offer_id = offer_id
        self.trade_price = trade_price
        self.trade_amount = trade_amount
        # tradeDate is different for both peers so we ignore it for hash
        self.trade_date = trade_date  # JsonExclude
        self.deposit_tx_id = deposit_tx_id  # JsonExclude

        # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
        # at the P2P network storage checks. The hash of the object will be used to verify if the data is valid. Any new
        # field in a class would break that hash and therefore break the storage mechanism.
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(
            extra_data_map
        )  # JsonExclude

        # Hash get set in constructor from json of all the other data fields (with hash = null).
        self.hash = (
            hash_bytes if hash_bytes is not None else self.create_hash()
        )  # JsonExclude
        # PB field signature_pub_key_bytes not used anymore from v0.6 on

    def get_json_dict(self):
        return {
            "direction": self.direction.name,
            "baseCurrency": self.base_currency,
            "counterCurrency": self.counter_currency,
            "offerPaymentMethod": self.offer_payment_method,
            "offerDate": self.offer_date,
            "offerUseMarketBasedPrice": self.offer_use_market_based_price,
            "offerMarketPriceMargin": self.offer_market_price_margin,
            "offerAmount": self.offer_amount,
            "offerMinAmount": self.offer_min_amount,
            "offerId": self.offer_id,
            "tradePrice": self.trade_price,
            "tradeAmount": self.trade_amount,
        }

    def create_hash(self):
        # We create hash from all fields excluding hash itself. We use json as simple data serialisation.
        # TradeDate is different for both peers so we ignore it for hash. ExtraDataMap is ignored as well as at
        # software updates we might have different entries which would cause a different hash.
        return get_sha256_ripemd160_hash(JsonUtil.object_to_json(self).encode("utf-8"))

    def get_builder(self):
        builder = protobuf.TradeStatistics2(
            direction=OfferDirection.to_proto_message(self.direction),
            base_currency=self.base_currency,
            counter_currency=self.counter_currency,
            payment_method_id=self.offer_payment_method,
            offer_date=self.offer_date,
            offer_use_market_based_price=self.offer_use_market_based_price,
            offer_market_price_margin=self.offer_market_price_margin,
            offer_amount=self.offer_amount,
            offer_min_amount=self.offer_min_amount,
            offer_id=self.offer_id,
            trade_price=self.trade_price,
            trade_amount=self.trade_amount,
            trade_date=self.trade_date,
            deposit_tx_id=self.deposit_tx_id,
            hash=self.hash,
        )
        if self.extra_data_map:
            builder.extra_data.update(self.extra_data_map)
        return builder

    def to_proto_trade_statistics_2(self):
        return self.get_builder()

    def to_proto_message(self):
        return protobuf.PersistableNetworkPayload(trade_statistics2=self.get_builder())

    @staticmethod
    def from_proto(proto: protobuf.TradeStatistics2):
        return TradeStatistics2(
            OfferDirection.from_proto(proto.direction),
            proto.base_currency,
            proto.counter_currency,
            proto.payment_method_id,
            proto.offer_date,
            proto.offer_use_market_based_price,
            proto.offer_market_price_margin,
            proto.offer_amount,
            proto.offer_min_amount,
            proto.offer_id,
            proto.trade_price,
            proto.trade_amount,
            proto.trade_date,
            ProtoUtil.string_or_none_from_proto(proto.deposit_tx_id),
            None,  # We want to clean up the hashes with the changed hash method in v.1.2.0 so we don't use the value from the proto
            dict(proto.extra_data) if proto.extra_data else None,
        )

    @staticmethod
    def from_trade(
        trade: "Trade", referral_id: Optional[str], is_tor_network_node: bool
    ):
        extra_data_map = dict[str, str]()
        if not referral_id:
            extra_data_map[OfferPayload.REFERRAL_ID] = referral_id

        mediator_node_address = trade.mediator_node_address
        if mediator_node_address is not None:
            # The first 4 chars are sufficient to identify a mediator.
            # For testing with regtest/localhost we use the full address as its localhost and would result in
            # same values for multiple mediators.
            truncated_mediator_address = (
                mediator_node_address.get_full_address()[:4]
                if is_tor_network_node
                else mediator_node_address.get_full_address()
            )
            extra_data_map[TradeStatistics2.MEDIATOR_ADDRESS] = (
                truncated_mediator_address
            )

        offer = trade.get_offer()
        assert offer is not None, "offer must not be None"
        assert trade.get_amount() is not None, "trade.get_amount() must not be None"
        offer_payload = offer.offer_payload
        assert offer_payload is not None, "offer_payload must not be None"
        return TradeStatistics2.from_offer_payload(
            offer_payload,
            trade.get_price(),
            trade.get_amount(),
            trade.get_date(),
            trade.deposit_tx_id,
            extra_data_map,
        )

    @staticmethod
    def from_offer_payload(
        self,
        offer_payload: OfferPayload,
        trade_price: Price,
        trade_amount: Coin,
        trade_date: datetime,
        deposit_tx_id: Optional[str],
        extra_data_map: dict,
    ):
        return TradeStatistics2(
            offer_payload.direction,
            offer_payload.base_currency_code,
            offer_payload.counter_currency_code,
            offer_payload.payment_method_id,
            offer_payload.date,
            offer_payload.use_market_based_price,
            offer_payload.market_price_margin,
            offer_payload.amount,
            offer_payload.min_amount,
            offer_payload.id,
            trade_price.value,
            trade_amount.value,
            int(trade_date.timestamp() * 1000),
            deposit_tx_id,
            None,
            extra_data_map,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_hash(self):
        return self.hash

    def verify_hash_size(self):
        assert self.hash is not None, "hash must not be None"
        return len(self.hash) == 20

    # With v1.2.0 we changed the way how the hash is created. To not create too heavy load for seed nodes from
    # requests from old nodes we use the TRADE_STATISTICS_HASH_UPDATE capability to send trade statistics only to new
    # nodes. As trade statistics are only used for informational purpose it will not have any critical issue for the
    # old nodes beside that they don't see the latest trades. We added TRADE_STATISTICS_HASH_UPDATE in v1.2.2 to fix a
    # problem of not handling the hashes correctly.
    def get_required_capabilities(self):
        return Capabilities([Capability.TRADE_STATISTICS_HASH_UPDATE])

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_trade_date(self):
        return datetime.fromtimestamp((self.trade_date / 1000), timezone.utc)

    def get_trade_price(self):
        return Price.value_of(self.get_currency_code(), self.trade_price)

    def get_currency_code(self):
        return (
            self.counter_currency if self.base_currency == "BTC" else self.base_currency
        )

    def get_trade_amount(self):
        return Coin.value_of(self.trade_amount)

    def get_trade_volume(self):
        price = self.get_trade_price()
        return (
            price.get_volume_by_amount(self.get_trade_amount())
            if isinstance(price.monetary, Altcoin)
            else VolumeUtil.get_rounded_fiat_volume(
                price.get_volume_by_amount(self.get_trade_amount())
            )
        )

    def is_valid(self):
        # Exclude a disputed BSQ trade where the price was off by a factor 10 due to a mistake by the maker.
        # Since the trade wasn't executed it's better to filter it out to avoid it having an undue influence on the
        # BSQ trade stats.
        excluded_failed_trade = (
            self.offer_id == "6E5KOI6O-3a06a037-6f03-4bfa-98c2-59f49f73466a-112"
        )
        deposit_tx_id_valid = self.deposit_tx_id is None or self.deposit_tx_id != ""
        return (
            self.trade_amount > 0
            and self.trade_price > 0
            and not excluded_failed_trade
            and deposit_tx_id_valid
        )

    def __lt__(self, other):
        # TODO: check if it's equivalent to java's sorting exactly
        if not isinstance(other, TradeStatistics2):
            return NotImplemented

        if (
            self.direction == other.direction
            and self.base_currency == other.base_currency
            and self.counter_currency == other.counter_currency
            and self.offer_payment_method == other.offer_payment_method
            and self.offer_date == other.offer_date
            and self.offer_use_market_based_price == other.offer_use_market_based_price
            and self.offer_amount == other.offer_amount
            and self.offer_min_amount == other.offer_min_amount
            and self.offer_id == other.offer_id
            and self.trade_price == other.trade_price
            and self.trade_amount == other.trade_amount
        ):
            return False

        return True

    def __eq__(self, other):
        if not isinstance(other, TradeStatistics2):
            return False

        return (
            self.direction == other.direction
            and self.base_currency == other.base_currency
            and self.counter_currency == other.counter_currency
            and self.offer_payment_method == other.offer_payment_method
            and self.offer_date == other.offer_date
            and self.offer_use_market_based_price == other.offer_use_market_based_price
            and self.offer_amount == other.offer_amount
            and self.offer_min_amount == other.offer_min_amount
            and self.offer_id == other.offer_id
            and self.trade_price == other.trade_price
            and self.trade_amount == other.trade_amount
        )

    def __str__(self):
        return (
            f"TradeStatistics2{{\n"
            f"     direction={self.direction},\n"
            f"     baseCurrency='{self.base_currency}',\n"
            f"     counterCurrency='{self.counter_currency}',\n"
            f"     offerPaymentMethod='{self.offer_payment_method}',\n"
            f"     offerDate={self.offer_date},\n"
            f"     offerUseMarketBasedPrice={self.offer_use_market_based_price},\n"
            f"     offerMarketPriceMargin={self.offer_market_price_margin},\n"
            f"     offerAmount={self.offer_amount},\n"
            f"     offerMinAmount={self.offer_min_amount},\n"
            f"     offerId='{self.offer_id}',\n"
            f"     tradePrice={self.trade_price},\n"
            f"     tradeAmount={self.trade_amount},\n"
            f"     tradeDate={self.trade_date},\n"
            f"     depositTxId='{self.deposit_tx_id}',\n"
            f"     hash={bytes_as_hex_string(self.hash)},\n"
            f"     extraDataMap={self.extra_data_map}\n"
            f"}}"
        )
