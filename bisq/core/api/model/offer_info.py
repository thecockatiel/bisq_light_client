from typing import TYPE_CHECKING
from bisq.common.payload import Payload
from bisq.common.util.math_utils import MathUtils
from bisq.core.monetary.price import Price
from bisq.core.offer.open_offer import OpenOffer
from bisq.core.util.coin.coin_util import CoinUtil
from bisq.core.util.price_util import PriceUtil
from bisq.core.util.volume_util import VolumeUtil
import grpc_pb2

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer


class OfferInfo(Payload):

    # The client cannot see bisq.core.Offer or its fromProto method.  We use the lighter
    # weight OfferInfo proto wrapper instead, containing just enough fields to view,
    # create and take offers.

    def __init__(
        self,
        id: str,
        direction: str,
        price: str,
        use_market_based_price: bool,
        market_price_margin_pct: float,
        amount: int,
        min_amount: int,
        volume: str,
        min_volume: str,
        tx_fee: int,
        maker_fee: int,
        offer_fee_payment_tx_id: str,
        buyer_security_deposit: int,
        seller_security_deposit: int,
        is_currency_for_maker_fee_btc: bool,
        payment_account_id: str,
        payment_method_id: str,
        payment_method_short_name: str,
        base_currency_code: str,
        counter_currency_code: str,
        date: int,
        state: str,
        is_my_offer: bool,
        is_bsq_swap_offer: bool,
        owner_node_address: str,
        pub_key_ring: str,
        version_number: str,
        protocol_version: int,
        trigger_price: str = "0",
        is_activated: bool = False,
        is_my_pending_offer: bool = False,
    ):
        self.id = id
        self.direction = direction
        self.price = price
        self.use_market_based_price = use_market_based_price
        self.market_price_margin_pct = market_price_margin_pct
        self.amount = amount
        self.min_amount = min_amount
        self.volume = volume
        self.min_volume = min_volume
        self.tx_fee = tx_fee
        self.maker_fee = maker_fee
        self.offer_fee_payment_tx_id = offer_fee_payment_tx_id
        self.buyer_security_deposit = buyer_security_deposit
        self.seller_security_deposit = seller_security_deposit
        self.trigger_price = trigger_price
        self.is_currency_for_maker_fee_btc = is_currency_for_maker_fee_btc
        self.payment_account_id = payment_account_id
        self.payment_method_id = payment_method_id
        self.payment_method_short_name = payment_method_short_name
        # Fiat offer:  baseCurrencyCode = BTC, counterCurrencyCode = fiat ccy code.
        # Altcoin offer:  baseCurrencyCode = altcoin ccy code, counterCurrencyCode = BTC.
        self.base_currency_code = base_currency_code
        self.counter_currency_code = counter_currency_code
        self.date = date
        self.state = state
        self.is_activated = is_activated
        self.is_my_offer = is_my_offer
        self.is_my_pending_offer = is_my_pending_offer
        self.is_bsq_swap_offer = is_bsq_swap_offer
        self.owner_node_address = owner_node_address
        self.pub_key_ring = pub_key_ring
        self.version_number = version_number
        self.protocol_version = protocol_version

    @classmethod
    def to_my_inactive_offer_info(cls, offer: "Offer"):
        offer_info = cls._from_offer(offer, is_my_offer=True)
        offer_info.is_activated = False
        return offer_info

    @classmethod
    def to_offer_info(cls, offer: "Offer"):
        # Assume the offer is not mine, but isMyOffer can be reset to true, i.e., when
        # calling TradeInfo toTradeInfo(Trade trade, String role, boolean isMyOffer);
        offer_info = cls._from_offer(offer, is_my_offer=False)
        offer_info.is_activated = True
        return offer_info

    @classmethod
    def to_my_pending_offer_info(cls, my_new_offer: "Offer"):
        # Use this to build an OfferInfo instance when a new OpenOffer is being
        # prepared, and no valid OpenOffer state (AVAILABLE, DEACTIVATED) exists.
        # It is needed for the CLI's 'createoffer' output, which has a boolean 'ENABLED'
        # column that will show a PENDING value when this.isMyPendingOffer = true.
        offer_info = cls._from_offer(my_new_offer, is_my_offer=True)
        offer_info.is_my_pending_offer = True
        offer_info.is_activated = False
        return offer_info

    @classmethod
    def to_my_offer_info(cls, open_offer: "OpenOffer"):
        # An OpenOffer is always my offer.
        offer = open_offer.offer
        currency_code = offer.currency_code
        is_activated = not open_offer.is_deactivated
        trigger_price = (
            Price.value_of(currency_code, open_offer.trigger_price)
            if not offer.is_bsq_swap_offer and open_offer.trigger_price > 0
            else None
        )
        precise_trigger_price = (
            PriceUtil.reformat_market_price(
                trigger_price.to_plain_string(), currency_code
            )
            if trigger_price is not None
            else "0"
        )
        offer_info = cls._from_offer(offer, is_my_offer=True)
        offer_info.trigger_price = precise_trigger_price
        offer_info.is_activated = is_activated
        return offer_info

    @staticmethod
    def _from_offer(offer: "Offer", is_my_offer: bool):
        # OfferInfo protos are passed to API client, and some field
        # values are converted to displayable, unambiguous form.
        currency_code = offer.currency_code
        assert (
            offer.get_price() is not None
        ), "offer.get_price() was None at OfferInfo._from_offer"
        precise_offer_price = PriceUtil.reformat_market_price(
            offer.get_price().to_plain_string(), currency_code
        )
        market_price_margin_as_pct_literal = MathUtils.exact_multiply(
            offer.market_price_margin, 100
        )
        assert (
            offer.volume is not None
        ), "offer.volume was None at OfferInfo._from_offer"
        assert (
            offer.min_volume is not None
        ), "offer.min_volume was None at OfferInfo._from_offer"
        rounded_volume = VolumeUtil.format_volume(offer.volume)
        rounded_min_volume = VolumeUtil.format_volume(offer.min_volume)

        return OfferInfo(
            id=offer.id,
            direction=offer.direction.name,
            price=precise_offer_price,
            use_market_based_price=offer.is_use_market_based_price,
            market_price_margin_pct=market_price_margin_as_pct_literal,
            amount=offer.amount.value,
            min_amount=offer.min_amount.value,
            volume=rounded_volume,
            min_volume=rounded_min_volume,
            tx_fee=offer.tx_fee.value,
            maker_fee=OfferInfo._get_maker_fee(offer, is_my_offer),
            offer_fee_payment_tx_id=offer.offer_fee_payment_tx_id,
            buyer_security_deposit=offer.buyer_security_deposit.value,
            seller_security_deposit=offer.seller_security_deposit.value,
            is_currency_for_maker_fee_btc=offer.is_currency_for_maker_fee_btc,
            payment_account_id=offer.maker_payment_account_id,
            payment_method_id=offer.payment_method.id,
            payment_method_short_name=offer.payment_method.get_short_name(),
            base_currency_code=offer.base_currency_code,
            counter_currency_code=offer.counter_currency_code,
            date=int(offer.date.timestamp() * 1000),
            state=offer.state.name,
            is_my_offer=is_my_offer,
            is_bsq_swap_offer=offer.is_bsq_swap_offer,
            owner_node_address=offer.offer_payload_base.get_owner_node_address().get_full_address(),
            pub_key_ring=str(offer.offer_payload_base.pub_key_ring),
            version_number=offer.offer_payload_base.version_nr,
            protocol_version=offer.offer_payload_base.protocol_version,
        )

    @staticmethod
    def _get_maker_fee(offer: "Offer", is_my_offer: bool) -> int:
        # JAVA TODO Find out why offer.maker_fee is always set to 0 when offer is bsq-swap.
        if is_my_offer:
            if offer.is_bsq_swap_offer:
                data = CoinUtil.get_maker_fee(False, offer.amount)
                assert (
                    data is not None
                ), "CoinUtil.get_maker_fee returned None at OfferInfo.get_maker_fee"
            else:
                offer.maker_fee.value
        else:
            return 0

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return grpc_pb2.OfferInfo(
            id=self.id,
            direction=self.direction,
            price=self.price,
            use_market_based_price=self.use_market_based_price,
            market_price_margin_pct=self.market_price_margin_pct,
            amount=self.amount,
            min_amount=self.min_amount,
            volume=self.volume if self.volume else "0",
            min_volume=self.min_volume if self.min_volume else "0",
            maker_fee=self.maker_fee,
            tx_fee=self.tx_fee,
            offer_fee_payment_tx_id=(
                "" if self.is_bsq_swap_offer else self.offer_fee_payment_tx_id
            ),
            buyer_security_deposit=self.buyer_security_deposit,
            seller_security_deposit=self.seller_security_deposit,
            trigger_price=self.trigger_price if self.trigger_price else "0",
            is_currency_for_maker_fee_btc=self.is_currency_for_maker_fee_btc,
            payment_account_id=self.payment_account_id,
            payment_method_id=self.payment_method_id,
            payment_method_short_name=self.payment_method_short_name,
            base_currency_code=self.base_currency_code,
            counter_currency_code=self.counter_currency_code,
            date=self.date,
            state=self.state,
            is_activated=self.is_activated,
            is_my_offer=self.is_my_offer,
            is_my_pending_offer=self.is_my_pending_offer,
            is_bsq_swap_offer=self.is_bsq_swap_offer,
            owner_node_address=self.owner_node_address,
            pub_key_ring=self.pub_key_ring,
            version_nr=self.version_number,
            protocol_version=self.protocol_version,
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.OfferInfo):
        return OfferInfo(
            id=proto.id,
            direction=proto.direction,
            price=proto.price,
            use_market_based_price=proto.use_market_based_price,
            market_price_margin_pct=proto.market_price_margin_pct,
            amount=proto.amount,
            min_amount=proto.min_amount,
            volume=proto.volume,
            min_volume=proto.min_volume,
            tx_fee=proto.tx_fee,
            maker_fee=proto.maker_fee,
            offer_fee_payment_tx_id=proto.offer_fee_payment_tx_id,
            buyer_security_deposit=proto.buyer_security_deposit,
            seller_security_deposit=proto.seller_security_deposit,
            is_currency_for_maker_fee_btc=proto.is_currency_for_maker_fee_btc,
            payment_account_id=proto.payment_account_id,
            payment_method_id=proto.payment_method_id,
            payment_method_short_name=proto.payment_method_short_name,
            base_currency_code=proto.base_currency_code,
            counter_currency_code=proto.counter_currency_code,
            date=proto.date,
            state=proto.state,
            is_activated=proto.is_activated,
            is_my_offer=proto.is_my_offer,
            is_my_pending_offer=proto.is_my_pending_offer,
            is_bsq_swap_offer=proto.is_bsq_swap_offer,
            owner_node_address=proto.owner_node_address,
            pub_key_ring=proto.pub_key_ring,
            version_number=proto.version_nr,
            protocol_version=proto.protocol_version,
            trigger_price=proto.trigger_price,
        )
