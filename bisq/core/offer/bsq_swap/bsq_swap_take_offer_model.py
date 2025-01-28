from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from bisq.core.offer.bsq_swap.bsq_swap_offer_model import BsqSwapOfferModel
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.trade.bisq_v1.trade_result_handler import TradeResultHandler
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.offer_util import OfferUtil
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.trade_manager import TradeManager

logger = get_logger(__name__)


class BsqSwapTakeOfferModel(BsqSwapOfferModel):
    def __init__(
        self,
        offer_util: "OfferUtil",
        btc_wallet_service: "BtcWalletService",
        bsq_wallet_service: "BsqWalletService",
        fee_service: "FeeService",
        trade_manager: "TradeManager",
        filter_manager: "FilterManager",
    ):
        super().__init__(
            offer_util, btc_wallet_service, bsq_wallet_service, fee_service
        )
        self.trade_manager = trade_manager
        self.filter_manager = filter_manager

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def init_with_data(self, offer: "Offer"):
        self.init(offer.direction, False, offer)
        self.offer = offer
        offer.reset_state()

    def do_activate(self):
        super().do_activate()
        self.trade_manager.check_offer_availability(
            self.offer, False, lambda: None, lambda error: logger.error(error)
        )

    def do_deactivate(self):
        super().do_deactivate()

        if self.offer is not None:
            self.offer.cancel_availability_request()

    def apply_amount(self, amount: Coin):
        self.set_btc_amount(
            Coin.value_of(min(amount.value, self.get_max_trade_limit()))
        )
        self.calculate_volume()
        self.calculate_input_and_payout()

    def on_take_offer(
        self,
        trade_result_handler: "TradeResultHandler[BsqSwapTrade]",
        warning_handler: "ErrorMessageHandler",
        error_handler: "ErrorMessageHandler",
        is_taker_api_user: bool,
    ):
        if self.filter_manager.is_currency_banned(self.offer.currency_code):
            warning_handler(Res.get("offerbook.warning.currencyBanned"))
        elif self.filter_manager.is_payment_method_banned(self.offer.payment_method):
            warning_handler(Res.get("offerbook.warning.paymentMethodBanned"))
        elif self.filter_manager.is_offer_id_banned(self.offer.id):
            warning_handler(Res.get("offerbook.warning.offerBlocked"))
        elif self.filter_manager.is_node_address_banned(self.offer.maker_node_address):
            warning_handler(Res.get("offerbook.warning.nodeBlocked"))
        elif self.filter_manager.require_update_to_new_version_for_trading():
            warning_handler(Res.get("offerbook.warning.requireUpdateToNewVersion"))
        elif self.trade_manager.was_offer_already_used_in_trade(self.offer.id):
            warning_handler(Res.get("offerbook.warning.offerWasAlreadyUsedInTrade"))
        else:
            self.trade_manager.on_take_bsq_swap_offer(
                self.offer,
                self.btc_amount_property.get(),
                self.tx_fee_per_vbyte,
                self.get_maker_fee().value,
                self.get_taker_fee().value,
                is_taker_api_user,
                trade_result_handler,
                error_handler,
            )
