from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.listeners.bsq_balance_listener import BsqBalanceListener
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.trade.model.bsq_swap.bsq_swap_calculation import BsqSwapCalculation
from bitcoinj.base.coin import Coin
from bitcoinj.wallet.listeners.wallet_change_event_listener import (
    WalletChangeEventListener,
)
from utils.data import SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bitcoinj.wallet.wallet import Wallet
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.offer.bsq_swap.open_bsq_swap_offer_service import (
        OpenBsqSwapOfferService,
    )
    from bisq.core.offer.open_offer import OpenOffer

logger = get_logger(__name__)


class OpenBsqSwapOffer:
    """
    Wrapper for OpenOffer listening for txFee and wallet changes.
    After a change event we recalculate the required funds and compare it with the available
    wallet funds. If not enough funds we set the bsqSwapOfferHasMissingFunds flag at
    openOffer and call the disableBsqSwapOffer at bsqSwapOpenOfferService.
    If we have been in the disabled state and we have now sufficient funds we call the
    enableBsqSwapOffer at bsqSwapOpenOfferService and update the
    bsqSwapOfferHasMissingFunds.
    """

    def __init__(
        self,
        open_offer: "OpenOffer",
        open_bsq_swap_offer_service: "OpenBsqSwapOfferService",
        fee_service: "FeeService",
        btc_wallet_service: "BtcWalletService",
        bsq_wallet_service: "BsqWalletService",
    ):
        self.open_offer = open_offer
        self.open_bsq_swap_offer_service = open_bsq_swap_offer_service
        self.fee_service = fee_service
        self.btc_wallet_service = btc_wallet_service
        self.bsq_wallet_service = bsq_wallet_service

        offer = open_offer.get_offer()
        self.is_buy_offer = offer.is_buy_offer
        self.fee_change_listener: Optional["SimplePropertyChangeEvent[int]"] = None
        self.bsq_balance_listener: Optional["BsqBalanceListener"] = None
        self.btc_wallet_change_event_listener: Optional["WalletChangeEventListener"] = (
            None
        )
        self.trade_fee = offer.maker_fee.get_value()
        self.btc_amount: Optional[Coin] = Coin.value_of(0)
        self.required_bsq_input: Optional[Coin] = Coin.value_of(0)

        self.tx_fee_per_vbyte = fee_service.get_tx_fee_per_vbyte().get_value()
        self.wallet_balance = Coin.value_of(0)
        self.has_missing_funds = False

        def _fee_change_listener(e: SimplePropertyChangeEvent[int]):
            new_tx_fee_per_vbyte = self.fee_service.get_tx_fee_per_vbyte().get_value()
            if new_tx_fee_per_vbyte != self.tx_fee_per_vbyte:
                self.tx_fee_per_vbyte = new_tx_fee_per_vbyte
                self._evaluate_funded_state()
                logger.info(
                    f"Updated because of fee change. tx_fee_per_vbyte={self.tx_fee_per_vbyte}, hasMissingFunds={self.has_missing_funds}"
                )

        self.fee_change_listener = _fee_change_listener

        self.fee_service.fee_update_counter_property.add_listener(
            self.fee_change_listener
        )

        if self.is_buy_offer:
            assert offer.volume is not None
            bsq_amount = BsqSwapCalculation.get_bsq_trade_amount(offer.volume)
            self.required_bsq_input = BsqSwapCalculation.get_buyers_bsq_input_value(
                bsq_amount.get_value(), self.trade_fee
            )
            self.wallet_balance = self.bsq_wallet_service.verified_balance

            def _bsq_balance_listener(
                available_balance: Coin,
                available_non_bsq_balance: Coin,
                unverified_balance: Coin,
                unconfirmed_change_balance: Coin,
                locked_for_voting_balance: Coin,
                locked_in_bonds_balance: Coin,
                unlocking_bonds_balance: Coin,
            ):
                if self.wallet_balance != available_balance:
                    self.wallet_balance = self.bsq_wallet_service.verified_balance
                    self._evaluate_funded_state()
                    self.apply_funding_state()
                    logger.info(
                        f"Updated because of BSQ wallet balance change. wallet_balance={self.wallet_balance}, has_missing_funds={self.has_missing_funds}"
                    )

            self.bsq_balance_listener = _bsq_balance_listener
            self.bsq_wallet_service.add_bsq_balance_listener(self.bsq_balance_listener)
            self.btc_wallet_change_event_listener = None
            self.btc_amount = None
        else:
            self.btc_amount = offer.amount
            self.wallet_balance = self.btc_wallet_service.get_saving_wallet_balance()

            def _btc_wallet_change_listener(wallet: "Wallet"):
                new_balance = self.btc_wallet_service.get_saving_wallet_balance()
                if self.wallet_balance != new_balance:
                    self.wallet_balance = new_balance
                    self._evaluate_funded_state()
                    self.apply_funding_state()
                    logger.info(
                        f"Updated because of BTC wallet balance change. wallet_balance={self.wallet_balance}, has_missing_funds={self.has_missing_funds}"
                    )

            self.btc_wallet_change_event_listener = _btc_wallet_change_listener
            self.btc_wallet_service.add_change_event_listener(
                self.btc_wallet_change_event_listener
            )
            self.bsq_balance_listener = None
            self.required_bsq_input = None

        # We might need to reset the state
        if self.open_offer.bsq_swap_offer_has_missing_funds:
            self.open_offer.state = OpenOfferState.AVAILABLE
            self.open_bsq_swap_offer_service.request_persistence()

        self._evaluate_funded_state()
        self.apply_funding_state()

    def remove_listeners(self):
        self.fee_service.fee_update_counter_property.remove_listener(
            self.fee_change_listener
        )
        if self.is_buy_offer:
            self.bsq_wallet_service.remove_bsq_balance_listener(
                self.bsq_balance_listener
            )
        else:
            self.btc_wallet_service.remove_change_event_listener(
                self.btc_wallet_change_event_listener
            )

    def apply_funding_state(self):
        prev = self.open_offer.bsq_swap_offer_has_missing_funds
        if self.has_missing_funds and not prev:
            self.open_offer.bsq_swap_offer_has_missing_funds = True
            self.open_bsq_swap_offer_service.request_persistence()

            if not self.open_offer.is_deactivated:
                self.open_bsq_swap_offer_service.disable_bsq_swap_offer(self.open_offer)

        elif not self.has_missing_funds and prev:
            self.open_offer.bsq_swap_offer_has_missing_funds = False
            self.open_bsq_swap_offer_service.request_persistence()

            if not self.open_offer.is_deactivated:
                self.open_bsq_swap_offer_service.enable_bsq_swap_offer(self.open_offer)

    def _evaluate_funded_state(self):
        if self.is_buy_offer:
            self.has_missing_funds = self.wallet_balance.is_less_than(
                self.required_bsq_input
            )
        else:
            try:
                required_input = (
                    BsqSwapCalculation.get_sellers_btc_input_value_from_wallet(
                        self.btc_wallet_service,
                        self.btc_amount,
                        self.tx_fee_per_vbyte,
                        self.trade_fee,
                    )
                )
                self.has_missing_funds = self.wallet_balance.is_less_than(
                    required_input
                )
            except Exception:  # TODO: InsufficientMoneyException
                self.has_missing_funds = True

    def __eq__(self, other):
        if self is other:
            return True
        if other is None or not isinstance(other, OpenBsqSwapOffer):
            return False
        return (
            self.trade_fee == other.trade_fee
            and self.is_buy_offer == other.is_buy_offer
            and self.open_offer == other.open_offer
            and self.btc_amount == other.btc_amount
            and self.required_bsq_input == other.required_bsq_input
        )

    def __hash__(self):
        return hash(
            (
                self.open_offer,
                self.trade_fee,
                self.is_buy_offer,
                self.btc_amount,
                self.required_bsq_input,
            )
        )
