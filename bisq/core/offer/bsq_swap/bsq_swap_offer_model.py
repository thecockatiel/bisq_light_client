from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.exceptions.insufficient_bsq_exception import InsufficientBsqException
from bisq.core.btc.listeners.balance_listener import BalanceListener
from bisq.core.btc.listeners.bsq_balance_listener import BsqBalanceListener
from bisq.core.monetary.price import Price
from bisq.core.monetary.volume import Volume
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.trade.model.bsq_swap.bsq_swap_calculation import BsqSwapCalculation
from bisq.core.util.coin.coin_util import CoinUtil
from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException
from utils.data import SimpleProperty
from bisq.core.offer.offer_util import OfferUtil

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.offer.offer import Offer

logger = get_logger(__name__)


class BsqSwapOfferModel:
    BSQ = "BSQ"

    def __init__(
        self,
        offer_util: "OfferUtil",
        btc_wallet_service: "BtcWalletService",
        bsq_wallet_service: "BsqWalletService",
        fee_service: "FeeService",
    ):
        self.offer_util = offer_util
        self.btc_wallet_service = btc_wallet_service
        self.bsq_wallet_service = bsq_wallet_service
        self.fee_service = fee_service

        # offer data
        self.offer_id: Optional[str] = None
        self.direction: Optional[OfferDirection] = None
        self.is_maker = False

        # amounts/price
        self.btc_amount_property = SimpleProperty[Optional[Coin]]()
        self.bsq_amount_property = SimpleProperty[Optional[Coin]]()
        self.min_amount_property = SimpleProperty[Optional[Coin]]()
        self.price_property = SimpleProperty[Optional[Price]]()
        self.volume_property = SimpleProperty[Optional[Volume]]()
        self.min_volume_property = SimpleProperty[Optional[Volume]]()
        self.input_amount_as_coin_property = SimpleProperty[Optional[Coin]]()
        self.payout_amount_as_coin_property = SimpleProperty[Optional[Coin]]()
        self.missing_funds_property = SimpleProperty[Coin](Coin.ZERO())
        self.tx_fee: Optional[Coin] = None
        self.tx_fee_per_vbyte: int = 0

        self._btc_balance_listener: Optional[Callable[[Coin], None]] = None
        self._bsq_balance_listener: Optional["BsqBalanceListener"] = None

    def _is_non_zero_amount(
        self, coin_property: SimpleProperty[Optional[Coin]]
    ) -> bool:
        return coin_property.get() is not None and not coin_property.get().is_zero()

    def _is_non_zero_price(
        self, price_property: SimpleProperty[Optional[Price]]
    ) -> bool:
        return price_property.get() is not None and not price_property.get().is_zero()

    def _is_non_zero_volume(
        self, volume_property: SimpleProperty[Optional[Volume]]
    ) -> bool:
        return volume_property.get() is not None and not volume_property.get().is_zero()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def init(
        self, direction: OfferDirection, is_maker: bool, offer: Optional["Offer"]
    ) -> None:
        self.direction = direction
        self.is_maker = is_maker

        if offer is not None:
            self.set_price(offer.get_price())

            self.set_btc_amount(
                Coin.value_of(min(offer.amount.value, self.get_max_trade_limit()))
            )
            self.calculate_volume_for_amount(self.btc_amount_property)

            self.set_min_amount(offer.min_amount)
            self.calculate_min_volume()

        self.create_listeners()
        self._apply_tx_fee_per_vbyte()

        self.calculate_volume()
        self.calculate_input_and_payout()

    def do_activate(self) -> None:
        self.add_listeners()

    def do_deactivate(self) -> None:
        self.remove_listeners()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_listeners(self) -> None:
        self._btc_balance_listener = lambda *_: self.calculate_input_and_payout()
        self._bsq_balance_listener = lambda *_: self.calculate_input_and_payout()

    def add_listeners(self) -> None:
        assert self._btc_balance_listener is not None
        assert self._bsq_balance_listener is not None
        self.btc_wallet_service.add_balance_listener(self._btc_balance_listener)
        self.bsq_wallet_service.add_bsq_balance_listener(self._bsq_balance_listener)

    def remove_listeners(self) -> None:
        assert self._btc_balance_listener is not None
        assert self._bsq_balance_listener is not None
        self.btc_wallet_service.remove_balance_listener(self._btc_balance_listener)
        self.bsq_wallet_service.remove_bsq_balance_listener(self._bsq_balance_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Calculations
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def calculate_volume(self) -> None:
        if self._is_non_zero_price(self.price_property) and self._is_non_zero_amount(
            self.btc_amount_property
        ):
            try:
                self.set_volume(
                    self.calculate_volume_for_amount(self.btc_amount_property)
                )
                self.calculate_min_volume()
            except Exception as e:
                logger.error(e)

    def calculate_min_volume(self) -> None:
        if self._is_non_zero_price(self.price_property) and self._is_non_zero_amount(
            self.min_amount_property
        ):
            try:
                self.min_volume_property.set(
                    self.calculate_volume_for_amount(self.min_amount_property)
                )
            except Exception as e:
                logger.error(e)

    def calculate_volume_for_amount(
        self, amount_property: SimpleProperty[Optional[Coin]]
    ) -> Optional[Volume]:
        assert self.price_property.get() is not None
        assert amount_property.get() is not None
        return self.price_property.get().get_volume_by_amount(amount_property.get())

    def calculate_amount(
        self, reduce_to_4_decimals_function: Callable[[Coin], Coin]
    ) -> None:
        if self._is_non_zero_price(self.price_property) and self._is_non_zero_volume(
            self.volume_property
        ):
            try:
                amount = self.price_property.get().get_amount_by_volume(
                    self.volume_property.get()
                )
                self.calculate_volume()
                self.btc_amount_property.set(reduce_to_4_decimals_function(amount))
                self._reset_tx_fee_and_missing_funds()

                self.calculate_input_and_payout()
            except Exception as e:
                logger.error(e)

    def calculate_input_and_payout(self) -> None:
        bsq_trade_amount_as_coin = self.bsq_amount_property.get()
        btc_trade_amount_as_coin = self.btc_amount_property.get()
        trade_fee_as_coin = self.get_trade_fee()
        if (
            bsq_trade_amount_as_coin is None
            or btc_trade_amount_as_coin is None
            or trade_fee_as_coin is None
        ):
            return
        trade_fee = trade_fee_as_coin.get_value()
        if self.is_buyer:
            self.input_amount_as_coin_property.set(
                BsqSwapCalculation.get_buyers_bsq_input_value(
                    bsq_trade_amount_as_coin.get_value(), trade_fee
                )
            )
            try:
                self.payout_amount_as_coin_property.set(
                    BsqSwapCalculation.get_buyers_btc_payout_value_from_wallet(
                        self.bsq_wallet_service,
                        bsq_trade_amount_as_coin,
                        btc_trade_amount_as_coin,
                        self.tx_fee_per_vbyte,
                        trade_fee,
                    )
                )
            except InsufficientBsqException:
                # As this is for the output we do not set the missingFunds here.

                # If we do not have sufficient funds we cannot calculate the required fee from the inputs and change,
                # so we use an estimated size for the tx fee.
                self.payout_amount_as_coin_property.set(
                    BsqSwapCalculation.get_estimated_buyers_btc_payout_value(
                        btc_trade_amount_as_coin, self.tx_fee_per_vbyte, trade_fee
                    )
                )
        else:
            try:
                self.input_amount_as_coin_property.set(
                    BsqSwapCalculation.get_sellers_btc_input_value_from_wallet(
                        self.btc_wallet_service,
                        btc_trade_amount_as_coin,
                        self.tx_fee_per_vbyte,
                        trade_fee,
                    )
                )
            except InsufficientMoneyException as e:
                self.missing_funds_property.set(e.missing)

                # If we do not have sufficient funds we cannot calculate the required fee from the inputs and change,
                # so we use an estimated size for the tx fee.
                self.input_amount_as_coin_property.set(
                    BsqSwapCalculation.get_estimated_sellers_btc_input_value(
                        btc_trade_amount_as_coin, self.tx_fee_per_vbyte, trade_fee
                    )
                )
            self.payout_amount_as_coin_property.set(
                BsqSwapCalculation.get_sellers_bsq_payout_value(
                    bsq_trade_amount_as_coin.get_value(), trade_fee
                )
            )
        self._evaluate_missing_funds()

    def _evaluate_missing_funds(self) -> None:
        wallet_balance = (
            self.bsq_wallet_service.verified_balance
            if self.is_buyer
            else self.btc_wallet_service.get_saving_wallet_balance()
        )
        self.missing_funds_property.set(
            self.offer_util.get_balance_shortage(
                self.input_amount_as_coin_property.get(), wallet_balance
            )
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Setters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def set_btc_amount(self, btc_amount: Coin) -> None:
        self.btc_amount_property.set(btc_amount)
        self._reset_tx_fee_and_missing_funds()

    def set_price(self, price: Price) -> None:
        self.price_property.set(price)

    def set_volume(self, volume: Volume) -> None:
        self.volume_property.set(volume)
        self.bsq_amount_property.set(
            BsqSwapCalculation.get_bsq_trade_amount(volume)
            if volume is not None
            else None
        )
        self._reset_tx_fee_and_missing_funds()

    def set_min_amount(self, min_amount: Coin) -> None:
        self.min_amount_property.set(min_amount)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx_fee(self) -> Optional[Coin]:
        if self.tx_fee is None:
            trade_fee_as_coin = self.get_trade_fee()
            if self.btc_amount_property.get() is None or trade_fee_as_coin is None:
                return self.tx_fee

            trade_fee = trade_fee_as_coin.get_value()
            if self.is_buyer:
                btc_inputs_and_change = (
                    BsqSwapCalculation.get_buyers_bsq_inputs_and_change(
                        self.bsq_wallet_service,
                        self.bsq_amount_property.get().get_value(),
                        trade_fee,
                    )
                )
            else:
                btc_inputs_and_change = (
                    BsqSwapCalculation.get_sellers_btc_inputs_and_change(
                        self.btc_wallet_service,
                        self.btc_amount_property.get().get_value(),
                        self.tx_fee_per_vbyte,
                        trade_fee,
                    )
                )
            vbytes = BsqSwapCalculation.get_vbytes_size(
                btc_inputs_and_change[0], btc_inputs_and_change[1].get_value()
            )
            adjusted_tx_fee = BsqSwapCalculation.get_adjusted_tx_fee(
                self.tx_fee_per_vbyte, vbytes, trade_fee
            )
            self.tx_fee = Coin.value_of(adjusted_tx_fee)
        return self.tx_fee

    def get_estimated_tx_fee(self) -> Coin:
        adjusted_tx_fee = BsqSwapCalculation.get_adjusted_tx_fee(
            self.tx_fee_per_vbyte,
            BsqSwapCalculation.ESTIMATED_VBYTES,
            self.get_trade_fee().get_value(),
        )
        return Coin.value_of(adjusted_tx_fee)

    def has_missing_funds(self) -> bool:
        self._evaluate_missing_funds()
        return self.missing_funds_property.get().is_positive()

    def get_trade_fee(self) -> Coin:
        return self.get_maker_fee() if self.is_maker else self.get_taker_fee()

    def get_taker_fee(self) -> Coin:
        return CoinUtil.get_taker_fee(False, self.btc_amount_property.get())

    def get_maker_fee(self) -> Coin:
        return CoinUtil.get_maker_fee(False, self.btc_amount_property.get())

    @property
    def is_buyer(self) -> bool:
        return self.is_buy_offer if self.is_maker else self.is_sell_offer

    @property
    def is_buy_offer(self) -> bool:
        return self.direction == OfferDirection.BUY

    @property
    def is_sell_offer(self) -> bool:
        return self.direction == OfferDirection.SELL

    @property
    def is_min_amount_less_or_equal_amount(self) -> bool:
        if (
            self.min_amount_property.get() is not None
            and self.btc_amount_property.get() is not None
        ):
            return not self.min_amount_property.get().is_greater_than(
                self.btc_amount_property.get()
            )
        return True

    def get_max_trade_limit(self) -> int:
        return PaymentMethod.BSQ_SWAP.get_max_trade_limit_as_coin(
            BsqSwapOfferModel.BSQ
        ).get_value()

    def get_missing_funds_as_coin(self) -> Coin:
        return (
            self.missing_funds_property.get()
            if self.missing_funds_property.get().is_positive()
            else Coin.ZERO()
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _apply_tx_fee_per_vbyte(self) -> None:
        # We only set the tx_fee_per_vbyte at start, otherwise we might get different required amounts while user has view open
        self.tx_fee_per_vbyte = self.fee_service.get_tx_fee_per_vbyte().get_value()
        self._reset_tx_fee_and_missing_funds()
        self.tx_fee_per_vbyte = self.fee_service.get_tx_fee_per_vbyte().get_value()
        self.calculate_input_and_payout()
        self._reset_tx_fee_and_missing_funds()

    def _reset_tx_fee_and_missing_funds(self) -> None:
        self.tx_fee = None
        self.missing_funds_property.set(Coin.ZERO())
