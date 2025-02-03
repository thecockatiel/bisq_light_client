from typing import TYPE_CHECKING
from bisq.core.api.model.contract_info import ContractInfo
from bisq.core.api.model.offer_info import OfferInfo
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.api.model.trade_info import TradeInfo

if TYPE_CHECKING:
    from bisq.core.offer.open_offer import OpenOffer


class CanceledTradeInfo:
    """Builds a TradeInfo instance from an OpenOffer with State = CANCELED."""

    def to_canceled_trade_info(my_canceled_open_offer: "OpenOffer") -> TradeInfo:
        if my_canceled_open_offer.state != OpenOfferState.CANCELED:
            raise IllegalArgumentException(
                f"offer '{my_canceled_open_offer.get_id()}' is not canceled"
            )

        offer = my_canceled_open_offer.offer
        offer_info = OfferInfo.to_my_inactive_offer_info(offer)

        return TradeInfo(
            offer=offer_info,
            trade_id=my_canceled_open_offer.get_id(),
            short_id=my_canceled_open_offer.get_short_id(),
            date=int(my_canceled_open_offer.get_date().timestamp() * 1000),
            role="",
            is_currency_for_taker_fee_btc=offer.is_currency_for_maker_fee_btc,
            tx_fee_as_long=offer.tx_fee.value,
            taker_fee_as_long=offer.maker_fee.value,
            taker_fee_tx_id="",  # Ignored
            deposit_tx_id="",  # Ignored
            payout_tx_id="",  # Ignored
            trade_amount_as_long=0,  # Ignored
            trade_price=offer_info.price,
            trade_volume="",  # Ignored
            trading_peer_node_address="",  # Ignored
            state="",  # Ignored
            phase="",  # Ignored
            trade_period_state="",  # Ignored
            is_deposit_published=False,  # Ignored
            is_deposit_confirmed=False,  # Ignored
            is_payment_started_message_sent=False,  # Ignored
            is_payment_received_message_sent=False,  # Ignored
            is_payout_published=False,  # Ignored
            is_completed=False,  # Ignored
            contract_as_json="",  # Ignored
            contract=ContractInfo.empty_contract(),  # Ignored
            closing_status=OpenOfferState.CANCELED.name.capitalize(),
        )
