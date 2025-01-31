from typing import TYPE_CHECKING, Optional, cast
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.exception.failed_precondition_exception import (
    FailedPreconditionException,
)
from bisq.core.api.exception.not_available_exception import NotAvailableException
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.model.trade_model import TradeModel
from bisq.core.trade.protocol.bisq_v1.buyer_protocol import BuyerProtocol
from bisq.core.trade.protocol.bisq_v1.seller_protocol import SellerProtocol
from bisq.core.util.validation.btc_address_validator import BtcAddressValidator
from bitcoinj.base.coin import Coin
from bisq.core.trade.model.bisq_v1.trade import Trade
import grpc_pb2

if TYPE_CHECKING:
    from bisq.core.btc.model.address_entry import AddressEntry
    from bisq.core.trade.model.tradable import Tradable
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.bisq_v1.trade_result_handler import TradeResultHandler
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
    from bisq.core.api.core_context import CoreContext
    from bisq.core.api.core_wallets_service import CoreWalletsService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.bisq_v1.take_offer_model import TakeOfferModel
    from bisq.core.offer.bsq_swap.bsq_swap_take_offer_model import BsqSwapTakeOfferModel
    from bisq.core.offer.offer_util import OfferUtil
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.bisq_v1.trade_util import TradeUtil
    from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import BsqSwapTradeManager
    from bisq.core.trade.closed_tradable_formatter import ClosedTradableFormatter
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.user.user import User

logger = get_logger(__name__)


class CoreTradesService:
    def __init__(
        self,
        core_context: "CoreContext",
        core_wallets_service: "CoreWalletsService",
        btc_wallet_service: "BtcWalletService",
        offer_util: "OfferUtil",
        bsq_swap_trade_manager: "BsqSwapTradeManager",
        closed_tradable_manager: "ClosedTradableManager",
        closed_tradable_formatter: "ClosedTradableFormatter",
        failed_trades_manager: "FailedTradesManager",
        take_offer_model: "TakeOfferModel",
        bsq_swap_take_offer_model: "BsqSwapTakeOfferModel",
        trade_manager: "TradeManager",
        trade_util: "TradeUtil",
        user: "User",
    ):
        self.core_context = core_context
        # Dependencies on core api services in this package must be kept to an absolute
        # minimum, but some trading functions require an unlocked wallet's key, so an
        # exception is made in this case.
        self.core_wallets_service = core_wallets_service
        self.btc_wallet_service = btc_wallet_service
        self.offer_util = offer_util
        self.bsq_swap_trade_manager = bsq_swap_trade_manager
        self.closed_tradable_manager = closed_tradable_manager
        self.closed_tradable_formatter = closed_tradable_formatter
        self.failed_trades_manager = failed_trades_manager
        self.take_offer_model = take_offer_model
        self.bsq_swap_take_offer_model = bsq_swap_take_offer_model
        self.trade_manager = trade_manager
        self.trade_util = trade_util
        self.user = user

    def take_bsq_swap_offer(
        self,
        offer: "Offer",
        intended_trade_amount: int,
        trade_result_handler: "TradeResultHandler[BsqSwapTrade]",
        error_message_handler: "ErrorMessageHandler",
    ):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        self._verify_intended_trade_amount_is_in_range(intended_trade_amount, offer)

        self.bsq_swap_take_offer_model.init_with_data(offer)
        self.bsq_swap_take_offer_model.apply_amount(
            Coin.value_of(intended_trade_amount)
        )

        # Block attempt to take swap offer if there are insufficient funds for the trade.
        missing_coin = self.bsq_swap_take_offer_model.get_missing_funds_as_coin()
        if missing_coin.value > 0:
            raise NotAvailableException(
                f"wallet has insufficient funds to take offer with id '{offer.id}'"
            )

        logger.info(
            f"Initiating take {'buy' if offer.is_buy_offer else 'sell'} offer, {self.bsq_swap_take_offer_model}"
        )
        self.bsq_swap_take_offer_model.on_take_offer(
            trade_result_handler,
            logger.warning,
            error_message_handler,
            self.core_context.is_api_user,
        )

    def take_offer(
        self,
        offer: "Offer",
        payment_account_id: str,
        taker_fee_currency_code: str,
        intended_trade_amount: int,
        result_handler: "TradeResultHandler[Trade]",
        error_message_handler: "ErrorMessageHandler",
    ):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        self.offer_util.maybe_set_fee_payment_currency_preference(
            taker_fee_currency_code
        )

        payment_account = self.user.get_payment_account(payment_account_id)
        if payment_account is None:
            raise ValueError(
                f"payment account with id '{payment_account_id}' not found"
            )

        self._verify_intended_trade_amount_is_in_range(intended_trade_amount, offer)

        use_savings_wallet = True

        self.take_offer_model.init_model(
            offer, payment_account, intended_trade_amount, use_savings_wallet
        )
        logger.info(
            f"Initiating take {'buy' if offer.is_buy_offer else 'sell'} offer, {self.take_offer_model}"
        )

        # Block attempt to take swap offer if there are insufficient funds for the trade.
        if not self.take_offer_model.is_btc_wallet_funded:
            raise NotAvailableException(
                f"wallet has insufficient btc to take offer with id '{offer.id}'"
            )

        self.trade_manager.on_take_offer(
            Coin.value_of(intended_trade_amount),
            self.take_offer_model.tx_fee_from_fee_service,
            self.take_offer_model.taker_fee,
            self.take_offer_model.is_currency_for_taker_fee_btc,
            offer.get_price().value,
            self.take_offer_model.get_funds_needed_for_trade(),
            offer,
            payment_account_id,
            use_savings_wallet,
            self.core_context.is_api_user,
            result_handler,
            error_message_handler,
        )

    def confirm_payment_started(
        self, trade_id: str, tx_id: Optional[str] = None, tx_key: Optional[str] = None
    ):
        trade = self.get_trade(trade_id)
        if self._is_following_buyer_protocol(trade):
            if not trade.is_deposit_confirmed:
                raise FailedPreconditionException(
                    f"cannot send a payment started message for trade '{trade.get_id()}' "
                    f"until trade deposit tx '{trade.deposit_tx_id}' is confirmed"
                )
            # pass along counter currency tx proof info if provided
            if tx_id and tx_key:
                trade.counter_currency_tx_id = tx_id
                trade.counter_currency_extra_data = tx_key
            trade_protocol = self.trade_manager.get_trade_protocol(trade)
            if not isinstance(trade_protocol, BuyerProtocol):
                raise IllegalStateException(
                    f"trade protocol for trade '{trade.get_id()}' is not a buyer protocol"
                )
            trade_protocol = cast(BuyerProtocol, trade_protocol)
            trade_protocol.on_payment_started(
                lambda: None,
                lambda error_message: (_ for _ in ()).throw(
                    IllegalStateException(error_message)
                ),
            )
        else:
            raise FailedPreconditionException(
                "you are the seller, and not sending payment"
            )
        
    def confirm_payment_received(self, trade_id: str):
        trade = self.get_trade(trade_id)
        if self._is_following_buyer_protocol(trade):
            raise FailedPreconditionException("you are the buyer, and not receiving payment")
        else:
            if not trade.is_deposit_confirmed:
                raise FailedPreconditionException(
                    f"cannot send a payment received message for trade '{trade.get_id()}' "
                    f"until trade deposit tx '{trade.deposit_tx_id}' is confirmed"
                )

            if not trade.is_fiat_sent:
                raise FailedPreconditionException(
                    f"cannot send a payment received confirmation message for trade '{trade.get_id()}' "
                    f"until after a trade payment started message has been sent"
                )
            trade_protocol = self.trade_manager.get_trade_protocol(trade)
            if not isinstance(trade_protocol, SellerProtocol):
                raise IllegalStateException(
                    f"trade protocol for trade '{trade.get_id()}' is not a seller protocol"
                )
            trade_protocol = cast(SellerProtocol, trade_protocol)
            trade_protocol.on_payment_received(
                lambda: None,
                lambda error_message: (_ for _ in ()).throw(IllegalStateException(error_message))
            )
        
    def close_trade(self, trade_id: str):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        self._verify_trade_is_not_closed(trade_id)
        trade = self._get_open_trade(trade_id)
        if trade is None:
            raise NotFoundException(f"trade with id '{trade_id}' not found")
        
        logger.info(f"Closing trade {trade_id}")
        self.trade_manager.on_trade_completed(trade)
    
    def withdraw_funds(self, trade_id: str, to_address: str, memo: str):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        self._verify_trade_is_not_closed(trade_id)
        trade = self._get_open_trade(trade_id)
        if trade is None:
            raise NotFoundException(f"trade with id '{trade_id}' not found")

        self._verify_is_valid_btc_address(to_address)

        from_address_entry = self.btc_wallet_service.get_or_create_address_entry(
            trade.get_id(), AddressEntryContext.TRADE_PAYOUT
        )
        self._verify_funds_not_withdrawn(from_address_entry)

        amount = trade.get_payout_amount()
        fee = self._get_estimated_tx_fee(from_address_entry.get_address_string(), to_address, amount)
        receiver_amount = amount.subtract(fee)

        logger.info(
            f"Withdrawing funds received from trade {trade_id}:"
            f"\n From {from_address_entry.get_address_string()}"
            f"\n To {to_address}"
            f"\n Amt {amount.to_friendly_string()}"
            f"\n Tx Fee {fee.to_friendly_string()}"
            f"\n Receiver Amt {receiver_amount.to_friendly_string()}"
            f"\n Memo {memo}"
        )
        self.trade_manager.on_withdraw_request(
            to_address,
            amount,
            fee,
            self.core_wallets_service.get_key(),
            trade,
            memo if memo else None,
            lambda: None,
            lambda error_message, exception: (
                logger.error(error_message, exc_info=exception),
                (_ for _ in ()).throw(IllegalStateException(error_message, exception))
            )
        )
        
    def get_trade_model(self, trade_id: str) -> "TradeModel":
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        open_trade = self._get_open_trade(trade_id)
        if open_trade is not None:
            return open_trade

        closed_trade = self._get_closed_trade(trade_id)
        if closed_trade is not None:
            return closed_trade

        bsq_swap_trade = self.bsq_swap_trade_manager.find_bsq_swap_trade_by_id(trade_id)
        if bsq_swap_trade is not None:
            return bsq_swap_trade

        raise NotFoundException(f"trade with id '{trade_id}' not found")
    
    def get_trade_role(self, trade_model: "TradeModel") -> str:
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()
        try:
            return self.trade_util.get_role(trade_model)
        except Exception as e:
            logger.error(f"Role not found for trade with Id {trade_model.get_id()}.", exc_info=e)
            return "Not Available"
        
    def get_trade(self, trade_id: str) -> "Trade":
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()
        trade = self._get_open_trade(trade_id)
        if trade is not None:
            return trade
        closed_trade = self._get_closed_trade(trade_id)
        if closed_trade is not None:
            return closed_trade
        raise NotFoundException(f"trade with id '{trade_id}' not found")

    def get_open_trades(self) -> list["TradeModel"]:
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()
        return list(self.trade_manager.get_trades()) # NOTE: why we make a copy again?

    def get_trade_history(
        self, category: grpc_pb2.GetTradesRequest.Category
    ) -> list["TradeModel"]:
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()
        if category == grpc_pb2.GetTradesRequest.Category.CLOSED:
            closed_trades = [
                t
                for t in self.closed_tradable_manager.get_closed_trades()
                if isinstance(t, TradeModel)
            ]
            closed_trades.extend(self.bsq_swap_trade_manager.get_bsq_swap_trades())
            return closed_trades
        else:
            failed_v1_trades = self.failed_trades_manager.get_trades()
            return list(failed_v1_trades)

    def fail_trade(self, trade_id: str):
        # JAVA TODO Recommend API users call this method with extra care because
        # the API lacks methods for diagnosing trade problems, and does not support
        # interaction with mediators. Users may accidentally fail valid trades,
        # although they can easily be un-failed with the 'un_fail_trade' method.
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        trade = self.get_trade(trade_id)
        self.trade_manager.on_move_invalid_trade_to_failed_trades(trade)
        logger.info(f"Trade {trade_id} changed to failed trade.")

    def unfail_trade(self, trade_id: str):
        self.core_wallets_service.verify_wallets_are_available()
        self.core_wallets_service.verify_encrypted_wallet_is_unlocked()

        failed_trade = self.failed_trades_manager.get_trade_by_id(trade_id)
        if failed_trade:
            self._verify_can_unfail_trade(failed_trade)
            self.failed_trades_manager.remove_trade(failed_trade)
            self.trade_manager.add_trade_to_pending_trades(failed_trade)
            logger.info(f"Failed trade {trade_id} changed to open trade.")
        else:
            raise NotFoundException(f"failed trade '{trade_id}' not found")

    def get_canceled_open_offers(self):
        return self.closed_tradable_manager.get_canceled_open_offers()

    def get_closed_trade_state_as_string(self, tradable: "Tradable"):
        return self.closed_tradable_formatter.get_state_as_string(tradable)

    def _get_open_trade(self, trade_id: str) -> Optional["Trade"]:
        return self.trade_manager.get_trade_by_id(trade_id)

    def _get_closed_trade(self, trade_id: str) -> Optional["Trade"]:
        tradable = self.closed_tradable_manager.get_tradable_by_id(trade_id)
        if tradable is not None and isinstance(tradable, Trade):
            return tradable
        return None

    def _is_following_buyer_protocol(self, trade: "Trade") -> bool:
        return isinstance(self.trade_manager.get_trade_protocol(trade), BuyerProtocol)

    def _get_estimated_tx_fee(
        self, from_address: str, to_address: str, amount: "Coin"
    ) -> "Coin":
        # JAVA TODO This and identical logic should be refactored into TradeUtil.
        try:
            return self.btc_wallet_service.get_fee_estimation_transaction(
                from_address, to_address, amount, AddressEntryContext.TRADE_PAYOUT
            ).fee
        except Exception as e:
            logger.error("", exc_info=e)
            raise IllegalStateException(f"could not estimate tx fee: {str(e)}")

    # Raises a RuntimeError trade is already closed.
    def _verify_trade_is_not_closed(self, trade_id: str):
        if self._get_closed_trade(trade_id) is not None:
            raise RuntimeError(f"trade '{trade_id}' is already closed")

    # Raises a RuntimeError if address is not valid.
    def _verify_is_valid_btc_address(self, address: str):
        try:
            BtcAddressValidator().validate(address)
        except Exception as e:
            logger.error("", exc_info=e)
            raise ValueError(f"'{address}' is not a valid btc address")

    # Raises a RuntimeError if address has a zero balance.
    def _verify_funds_not_withdrawn(self, from_address_entry: "AddressEntry"):
        from_address_balance = self.btc_wallet_service.get_balance_for_address(
            from_address_entry.get_address()
        )
        if from_address_balance.is_zero():
            raise IllegalStateException(
                f"funds already withdrawn from address '{from_address_entry.get_address_string()}'"
            )

    # Raises a RuntimeError if failed trade cannot be changed to OPEN for any reason.
    def _verify_can_unfail_trade(self, failed_trade: "Trade"):
        if self.trade_util.get_trade_addresses(failed_trade) is None:
            raise IllegalStateException(
                f"cannot change failed trade to open because no trade addresses found for '{failed_trade.get_id()}'"
            )

        if not self.failed_trades_manager.has_deposit_tx(failed_trade):
            raise IllegalStateException(
                f"cannot change failed trade to open, no deposit tx found for '{failed_trade.get_id()}'"
            )

        if not self.failed_trades_manager.has_delayed_payout_tx_bytes(failed_trade):
            raise IllegalStateException(
                f"cannot change failed trade to open, no delayed payout tx found for '{failed_trade.get_id()}'"
            )

        blocking_trade_ids = self.failed_trades_manager.get_blocking_trade_ids(
            failed_trade
        )
        if blocking_trade_ids:
            trade_ids_str = ", ".join(blocking_trade_ids)
            raise IllegalStateException(
                f"cannot change failed trade '{failed_trade.get_id()}' to open at this time,\n"
                f"try again after completing trade(s):\n\t{trade_ids_str}"
            )

    # Throws a RuntimeError if the takeoffer's amount parameter is out of range.
    def _verify_intended_trade_amount_is_in_range(
        self, intended_trade_amount: int, offer: "Offer"
    ):
        if (
            intended_trade_amount < offer.min_amount.value
            or intended_trade_amount > offer.amount.value
        ):
            raise ValueError(
                f"intended trade amount {Coin.value_of(intended_trade_amount).to_plain_string().lower()} "
                f"is outside offer's min - max amount range of "
                f"{offer.min_amount.to_plain_string().lower()} - {offer.amount.to_plain_string().lower()}"
            )
