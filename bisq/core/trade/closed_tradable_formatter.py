from typing import TYPE_CHECKING, cast

from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.locale.res import Res
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.trade.closed_tradable_util import (
    cast_to_bsq_swap_trade,
    cast_to_open_offer,
    cast_to_trade,
    get_total_volume_by_currency,
    get_tx_fee,
    is_bisq_v1_trade,
    is_bsq_swap_trade,
    is_open_offer,
)
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.util.formatting_util import FormattingUtils
from bisq.core.util.price_util import PriceUtil
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType


if TYPE_CHECKING:
    from bisq.core.trade.model.tradable import Tradable
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.util.coin.bsq_formatter import BsqFormatter
    from bisq.core.util.coin.coin_formatter import CoinFormatter

logger = get_logger(__name__)


class ClosedTradableFormatter:
    # Resource bundle i18n keys with Desktop UI specific property names,
    # having "generic-enough" property values to be referenced in the core layer.
    I18N_KEY_TOTAL_AMOUNT = "closedTradesSummaryWindow.totalAmount.value"
    I18N_KEY_TOTAL_TX_FEE = "closedTradesSummaryWindow.totalMinerFee.value"
    I18N_KEY_TOTAL_TRADE_FEE_BTC = "closedTradesSummaryWindow.totalTradeFeeInBtc.value"
    I18N_KEY_TOTAL_TRADE_FEE_BSQ = "closedTradesSummaryWindow.totalTradeFeeInBsq.value"

    def __init__(
        self,
        closed_tradable_manager: "ClosedTradableManager",
        bsq_formatter: "BsqFormatter",
        btc_formatter: "CoinFormatter",
        bsq_wallet_service: "BsqWalletService",
    ):
        self.closed_tradable_manager = closed_tradable_manager
        self.bsq_formatter = bsq_formatter
        self.btc_formatter = btc_formatter
        self.bsq_wallet_service = bsq_wallet_service

    def get_amount_as_string(self, tradable: "Tradable"):
        amount = tradable.get_optional_amount()
        if amount is not None:
            return self.btc_formatter.format_coin(amount)
        else:
            return ""

    def get_total_amount_with_volume_as_string(self, total_trade_amount: Coin, volume):
        return Res.get(
            self.I18N_KEY_TOTAL_AMOUNT,
            self.btc_formatter.format_coin(total_trade_amount, append_code=True),
            VolumeUtil.format_volume_with_code(volume),
        )

    def get_tx_fee_as_string(self, tradable: "Tradable"):
        return self.btc_formatter.format_coin(get_tx_fee(tradable))

    def get_total_tx_fee_as_string(self, total_trade_amount: Coin, total_tx_fee: Coin):
        if abs(total_trade_amount.value) > 0:
            percentage = total_tx_fee.value / total_trade_amount.value
        else:
            percentage = 0

        return Res.get(
            ClosedTradableFormatter.I18N_KEY_TOTAL_TX_FEE,
            self.btc_formatter.format_coin(total_tx_fee, append_code=True),
            FormattingUtils.format_to_percent_with_symbol(percentage),
        )

    def get_buyer_security_deposit_as_string(self, tradable: "Tradable"):
        if is_bsq_swap_trade(tradable):
            return Res.get("shared.na")
        return self.btc_formatter.format_coin(
            tradable.get_offer().buyer_security_deposit
        )

    def get_seller_security_deposit_as_string(self, tradable: "Tradable"):
        if is_bsq_swap_trade(tradable):
            return Res.get("shared.na")
        return self.btc_formatter.format_coin(
            tradable.get_offer().seller_security_deposit
        )

    def get_total_trade_fee_in_bsq_as_string(
        self,
        total_trade_fee: Coin,
        trade_amount_volume: Volume,
        bsq_volume_in_usd: Volume,
    ):
        if abs(trade_amount_volume.value) > 0:
            percentage = bsq_volume_in_usd.value / trade_amount_volume.value
        else:
            percentage = 0

        return Res.get(
            ClosedTradableFormatter.I18N_KEY_TOTAL_TRADE_FEE_BSQ,
            self.bsq_formatter.format_coin(total_trade_fee, append_code=True),
            FormattingUtils.format_to_percent_with_symbol(percentage),
        )

    def get_trade_fee_as_string(self, tradable: "Tradable", append_code: bool):
        if self.closed_tradable_manager.is_bsq_trade_fee(tradable):
            return self.bsq_formatter.format_coin(
                Coin.value_of(self.closed_tradable_manager.get_bsq_trade_fee(tradable)),
                append_code=append_code,
            )
        else:
            return self.btc_formatter.format_coin(
                Coin.value_of(self.closed_tradable_manager.get_btc_trade_fee(tradable)),
                append_code=append_code,
            )

    def get_total_trade_fee_in_btc_as_string(
        self, total_trade_amount: Coin, total_trade_fee: Coin
    ):
        if abs(total_trade_amount.value) > 0:
            percentage = total_trade_fee.value / total_trade_amount.value
        else:
            percentage = 0

        return Res.get(
            ClosedTradableFormatter.I18N_KEY_TOTAL_TRADE_FEE_BTC,
            self.btc_formatter.format_coin(total_trade_fee, append_code=True),
            FormattingUtils.format_to_percent_with_symbol(percentage),
        )

    def get_price_deviation_as_string(self, tradable: "Tradable"):
        deviation = PriceUtil.offer_percentage_to_deviation(tradable.get_offer())
        if deviation is not None:
            return FormattingUtils.format_percentage_price(deviation)
        else:
            return Res.get("shared.na")

    def get_volume_as_string(self, tradable: "Tradable", append_code: bool):
        volume = tradable.get_optional_volume()
        if volume is not None:
            return VolumeUtil.format_volume(volume, append_currency_code=append_code)
        else:
            return ""

    def get_volume_currency_as_string(self, tradable: "Tradable"):
        volume = tradable.get_optional_volume()
        if volume is not None:
            return volume.currency_code
        else:
            return ""

    def get_price_as_string(self, tradable: "Tradable"):
        price = tradable.get_optional_price()
        if price is not None:
            return FormattingUtils.format_price(price)
        else:
            return ""

    def get_total_volume_by_currency_as_string(
        self, tradable_list: list["Tradable"]
    ) -> dict[str, str]:
        total_volume_by_currency = get_total_volume_by_currency(tradable_list)
        result = {}
        for currency_code, amount in total_volume_by_currency.items():
            if is_crypto_currency(currency_code):
                monetary = Altcoin.value_of(currency_code, amount)
            else:
                monetary = Fiat.value_of(currency_code, amount)
            result[currency_code] = VolumeUtil.format_volume_with_code(Volume(monetary))
        return result

    def get_state_as_string(self, tradable: "Tradable") -> str:
        if tradable is None:
            return ""

        if is_bisq_v1_trade(tradable):
            trade = cast_to_trade(tradable)
            if trade.is_withdrawn or trade.is_payout_published:
                return Res.get("portfolio.closed.completed")
            elif trade.dispute_state == TradeDisputeState.DISPUTE_CLOSED:
                return Res.get("portfolio.closed.ticketClosed")
            elif trade.dispute_state == TradeDisputeState.MEDIATION_CLOSED:
                return Res.get("portfolio.closed.mediationTicketClosed")
            elif trade.dispute_state == TradeDisputeState.REFUND_REQUEST_CLOSED:
                return Res.get("portfolio.closed.ticketClosed")
            else:
                logger.error(
                    f"That must not happen. We got a pending state but we are in the closed trades list. state={trade.get_trade_state().name}"
                )
                return Res.get("shared.na")
        elif is_open_offer(tradable):
            state = cast_to_open_offer(tradable).state
            logger.trace(f"OpenOffer state={state.name}")
            if state in [
                OpenOfferState.AVAILABLE,
                OpenOfferState.RESERVED,
                OpenOfferState.CLOSED,
                OpenOfferState.DEACTIVATED,
            ]:
                logger.error(f"Invalid state {state.name}")
                return state.name
            elif state == OpenOfferState.CANCELED:
                return Res.get("portfolio.closed.canceled")
            else:
                logger.error(f"Unhandled state {state.name}")
                return state.name
        elif is_bsq_swap_trade(tradable):
            tx_id = cast_to_bsq_swap_trade(tradable).tx_id
            confidence = self.bsq_wallet_service.get_confidence_for_tx_id(tx_id)
            if (
                confidence is not None
                and confidence.confidence_type == TransactionConfidenceType.BUILDING
            ):
                return Res.get("confidence.confirmed.short")
            elif (
                confidence is not None
                and confidence.confidence_type == TransactionConfidenceType.PENDING
            ):
                return Res.get("confidence.pending")
            else:
                logger.warning(
                    f"Unexpected confidence in a BSQ swap trade which has been moved to closed trades. "
                    f"This could happen at a wallet SPV resync or a reorg. confidence={confidence} tradeID={tradable.get_id()}"
                )
        return Res.get("shared.na")
