from typing import TYPE_CHECKING, Optional, cast
from bisq.core.api.exception.failed_precondition_exception import (
    FailedPreconditionException,
)
from bisq.core.api.exception.not_available_exception import NotAvailableException
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
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
    from bisq.core.user.user_context import UserContext


class CoreTradesService:
    def __init__(
        self,
        core_context: "CoreContext",
        core_wallets_service: "CoreWalletsService",
    ):
        self._core_context = core_context
        # Dependencies on core api services in this package must be kept to an absolute
        # minimum, but some trading functions require an unlocked wallet's key, so an
        # exception is made in this case.
        self._core_wallets_service = core_wallets_service

    def take_bsq_swap_offer(
        self,
        user_context: "UserContext",
        offer: "Offer",
        intended_trade_amount: int,
        trade_result_handler: "TradeResultHandler[BsqSwapTrade]",
        error_message_handler: "ErrorMessageHandler",
    ):
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        self._verify_intended_trade_amount_is_in_range(intended_trade_amount, offer)

        c.bsq_swap_take_offer_model.init_with_data(offer)
        c.bsq_swap_take_offer_model.apply_amount(Coin.value_of(intended_trade_amount))

        # Block attempt to take swap offer if there are insufficient funds for the trade.
        missing_coin = c.bsq_swap_take_offer_model.get_missing_funds_as_coin()
        if missing_coin.value > 0:
            raise NotAvailableException(
                f"wallet has insufficient funds to take offer with id '{offer.id}'"
            )

        user_context.logger.info(
            f"Initiating take {'buy' if offer.is_buy_offer else 'sell'} offer, {c.bsq_swap_take_offer_model}"
        )
        c.bsq_swap_take_offer_model.on_take_offer(
            trade_result_handler,
            user_context.logger.warning,
            error_message_handler,
            self._core_context.is_api_user,
        )

    def take_offer(
        self,
        user_context: "UserContext",
        offer: "Offer",
        payment_account_id: str,
        taker_fee_currency_code: str,
        intended_trade_amount: int,
        result_handler: "TradeResultHandler[Trade]",
        error_message_handler: "ErrorMessageHandler",
    ):
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        c.offer_util.maybe_set_fee_payment_currency_preference(taker_fee_currency_code)

        payment_account = c.user.get_payment_account(payment_account_id)
        if payment_account is None:
            raise IllegalArgumentException(
                f"payment account with id '{payment_account_id}' not found"
            )

        self._verify_intended_trade_amount_is_in_range(intended_trade_amount, offer)

        use_savings_wallet = True

        c.take_offer_model.init_model(
            offer, payment_account, intended_trade_amount, use_savings_wallet
        )
        user_context.logger.info(
            f"Initiating take {'buy' if offer.is_buy_offer else 'sell'} offer, {c.take_offer_model}"
        )

        # Block attempt to take swap offer if there are insufficient funds for the trade.
        if not c.take_offer_model.is_btc_wallet_funded:
            raise NotAvailableException(
                f"wallet has insufficient btc to take offer with id '{offer.id}'"
            )

        c.trade_manager.on_take_offer(
            Coin.value_of(intended_trade_amount),
            c.take_offer_model.tx_fee_from_fee_service,
            c.take_offer_model.taker_fee,
            c.take_offer_model.is_currency_for_taker_fee_btc,
            offer.get_price().value,
            c.take_offer_model.get_funds_needed_for_trade(),
            offer,
            payment_account_id,
            use_savings_wallet,
            self._core_context.is_api_user,
            result_handler,
            error_message_handler,
        )

    def confirm_payment_started(
        self,
        user_context: "UserContext",
        trade_id: str,
        tx_id: Optional[str] = None,
        tx_key: Optional[str] = None,
    ):
        c = user_context.global_container
        trade = self.get_trade(user_context, trade_id)
        if self._is_following_buyer_protocol(user_context, trade):
            if not trade.is_deposit_confirmed:
                raise FailedPreconditionException(
                    f"cannot send a payment started message for trade '{trade.get_id()}' "
                    f"until trade deposit tx '{trade.deposit_tx_id}' is confirmed"
                )
            # pass along counter currency tx proof info if provided
            if tx_id and tx_key:
                trade.counter_currency_tx_id = tx_id
                trade.counter_currency_extra_data = tx_key
            trade_protocol = c.trade_manager.get_trade_protocol(trade)
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

    def confirm_payment_received(self, user_context: "UserContext", trade_id: str):
        c = user_context.global_container
        trade = self.get_trade(user_context, trade_id)
        if self._is_following_buyer_protocol(user_context, trade):
            raise FailedPreconditionException(
                "you are the buyer, and not receiving payment"
            )
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
            trade_protocol = c.trade_manager.get_trade_protocol(trade)
            if not isinstance(trade_protocol, SellerProtocol):
                raise IllegalStateException(
                    f"trade protocol for trade '{trade.get_id()}' is not a seller protocol"
                )
            trade_protocol = cast(SellerProtocol, trade_protocol)
            trade_protocol.on_payment_received(
                lambda: None,
                lambda error_message: (_ for _ in ()).throw(
                    IllegalStateException(error_message)
                ),
            )

    def close_trade(self, user_context: "UserContext", trade_id: str):
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        self._verify_trade_is_not_closed(user_context, trade_id)
        trade = self._get_open_trade(user_context, trade_id)
        if trade is None:
            raise NotFoundException(f"trade with id '{trade_id}' not found")

        user_context.logger.info(f"Closing trade {trade_id}")
        c.trade_manager.on_trade_completed(trade)

    def withdraw_funds(
        self, user_context: "UserContext", trade_id: str, to_address: str, memo: str
    ):
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        self._verify_trade_is_not_closed(user_context, trade_id)
        trade = self._get_open_trade(user_context, trade_id)
        if trade is None:
            raise NotFoundException(f"trade with id '{trade_id}' not found")

        self._verify_is_valid_btc_address(user_context, to_address)

        from_address_entry = c.btc_wallet_service.get_or_create_address_entry(
            trade.get_id(), AddressEntryContext.TRADE_PAYOUT
        )
        self._verify_funds_not_withdrawn(user_context, from_address_entry)

        amount = trade.get_payout_amount()
        fee = self._get_estimated_tx_fee(
            user_context,
            from_address_entry.get_address_string(),
            to_address,
            amount,
        )
        receiver_amount = amount.subtract(fee)

        user_context.logger.info(
            f"Withdrawing funds received from trade {trade_id}:"
            f"\n From {from_address_entry.get_address_string()}"
            f"\n To {to_address}"
            f"\n Amt {amount.to_friendly_string()}"
            f"\n Tx Fee {fee.to_friendly_string()}"
            f"\n Receiver Amt {receiver_amount.to_friendly_string()}"
            f"\n Memo {memo}"
        )
        c.trade_manager.on_withdraw_request(
            to_address,
            amount,
            fee,
            self._core_wallets_service.get_key(user_context),
            trade,
            memo if memo else None,
            lambda: None,
            lambda error_message, exception: (
                user_context.logger.error(error_message, exc_info=exception),
                (_ for _ in ()).throw(IllegalStateException(error_message, exception)),
            ),
        )

    def get_trade_model(
        self, user_context: "UserContext", trade_id: str
    ) -> "TradeModel":
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        open_trade = self._get_open_trade(user_context, trade_id)
        if open_trade is not None:
            return open_trade

        closed_trade = self._get_closed_trade(user_context, trade_id)
        if closed_trade is not None:
            return closed_trade

        bsq_swap_trade = c.bsq_swap_trade_manager.find_bsq_swap_trade_by_id(trade_id)
        if bsq_swap_trade is not None:
            return bsq_swap_trade

        raise NotFoundException(f"trade with id '{trade_id}' not found")

    def get_trade_role(
        self, user_context: "UserContext", trade_model: "TradeModel"
    ) -> str:
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container
        try:
            return c.trade_util.get_role(trade_model)
        except Exception as e:
            user_context.logger.error(
                f"Role not found for trade with Id {trade_model.get_id()}.", exc_info=e
            )
            return "Not Available"

    def get_trade(self, user_context: "UserContext", trade_id: str) -> "Trade":
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        trade = self._get_open_trade(user_context, trade_id)
        if trade is not None:
            return trade
        closed_trade = self._get_closed_trade(user_context, trade_id)
        if closed_trade is not None:
            return closed_trade
        raise NotFoundException(f"trade with id '{trade_id}' not found")

    def get_open_trades(self, user_context: "UserContext") -> list["TradeModel"]:
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        return list(
            user_context.global_container.trade_manager.get_trades()  # NOTE: why we make a copy again?
        )

    def get_trade_history(
        self, user_context: "UserContext", category: grpc_pb2.GetTradesRequest.Category
    ) -> list["TradeModel"]:
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container
        if category == grpc_pb2.GetTradesRequest.Category.CLOSED:
            closed_trades = [
                t
                for t in c.closed_tradable_manager.get_closed_trades()
                if isinstance(t, TradeModel)
            ]
            closed_trades.extend(c.bsq_swap_trade_manager.get_bsq_swap_trades())
            return closed_trades
        else:
            failed_v1_trades = c.failed_trades_manager.get_trades()
            return list(failed_v1_trades)

    def fail_trade(self, user_context: "UserContext", trade_id: str):
        # JAVA TODO Recommend API users call this method with extra care because
        # the API lacks methods for diagnosing trade problems, and does not support
        # interaction with mediators. Users may accidentally fail valid trades,
        # although they can easily be un-failed with the 'unfail_trade' method.
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        trade = self.get_trade(user_context, trade_id)
        c.trade_manager.on_move_invalid_trade_to_failed_trades(trade)
        user_context.logger.info(f"Trade {trade_id} changed to failed trade.")

    def unfail_trade(self, user_context: "UserContext", trade_id: str):
        self._core_wallets_service.verify_wallets_are_available(user_context)
        self._core_wallets_service.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        failed_trade = c.failed_trades_manager.get_trade_by_id(trade_id)
        if failed_trade:
            self._verify_can_unfail_trade(user_context, failed_trade)
            c.failed_trades_manager.remove_trade(failed_trade)
            c.trade_manager.add_trade_to_pending_trades(failed_trade)
            user_context.logger.info(f"Failed trade {trade_id} changed to open trade.")
        else:
            raise NotFoundException(f"failed trade '{trade_id}' not found")

    def get_canceled_open_offers(self, user_context: "UserContext"):
        c = user_context.global_container
        return c.closed_tradable_manager.get_canceled_open_offers()

    def get_closed_trade_state_as_string(
        self, user_context: "UserContext", tradable: "Tradable"
    ):
        c = user_context.global_container
        return c.closed_tradable_formatter.get_state_as_string(tradable)

    def _get_open_trade(
        self, user_context: "UserContext", trade_id: str
    ) -> Optional["Trade"]:
        return user_context.global_container.trade_manager.get_trade_by_id(trade_id)

    def _get_closed_trade(
        self, user_context: "UserContext", trade_id: str
    ) -> Optional["Trade"]:
        tradable = (
            user_context.global_container.closed_tradable_manager.get_tradable_by_id(
                trade_id
            )
        )
        if tradable is not None and isinstance(tradable, Trade):
            return tradable
        return None

    def _is_following_buyer_protocol(
        self, user_context: "UserContext", trade: "Trade"
    ) -> bool:
        return isinstance(
            user_context.global_container.trade_manager.get_trade_protocol(trade),
            BuyerProtocol,
        )

    def _get_estimated_tx_fee(
        self,
        user_context: "UserContext",
        from_address: str,
        to_address: str,
        amount: "Coin",
    ) -> "Coin":
        # JAVA TODO This and identical logic should be refactored into TradeUtil.
        try:
            return user_context.global_container.btc_wallet_service.get_fee_estimation_transaction(
                from_address, to_address, amount, AddressEntryContext.TRADE_PAYOUT
            ).get_fee()
        except Exception as e:
            user_context.logger.error("", exc_info=e)
            raise IllegalStateException(f"could not estimate tx fee: {str(e)}")

    # Raises a RuntimeError trade is already closed.
    def _verify_trade_is_not_closed(self, user_context: "UserContext", trade_id: str):
        if self._get_closed_trade(user_context, trade_id) is not None:
            raise IllegalArgumentException(f"trade '{trade_id}' is already closed")

    # Raises a RuntimeError if address is not valid.
    def _verify_is_valid_btc_address(self, user_context: "UserContext", address: str):
        try:
            BtcAddressValidator().validate(address)
        except Exception as e:
            user_context.logger.error("", exc_info=e)
            raise IllegalArgumentException(f"'{address}' is not a valid btc address")

    # Raises a RuntimeError if address has a zero balance.
    def _verify_funds_not_withdrawn(
        self, user_context: "UserContext", from_address_entry: "AddressEntry"
    ):
        from_address_balance = (
            user_context.global_container.btc_wallet_service.get_balance_for_address(
                from_address_entry.get_address()
            )
        )
        if from_address_balance.is_zero():
            raise IllegalStateException(
                f"funds already withdrawn from address '{from_address_entry.get_address_string()}'"
            )

    # Raises a RuntimeError if failed trade cannot be changed to OPEN for any reason.
    def _verify_can_unfail_trade(
        self, user_context: "UserContext", failed_trade: "Trade"
    ):
        c = user_context.global_container
        if c.trade_util.get_trade_addresses(failed_trade) is None:
            raise IllegalStateException(
                f"cannot change failed trade to open because no trade addresses found for '{failed_trade.get_id()}'"
            )

        if not c.failed_trades_manager.has_deposit_tx(failed_trade):
            raise IllegalStateException(
                f"cannot change failed trade to open, no deposit tx found for '{failed_trade.get_id()}'"
            )

        if not c.failed_trades_manager.has_delayed_payout_tx_bytes(failed_trade):
            raise IllegalStateException(
                f"cannot change failed trade to open, no delayed payout tx found for '{failed_trade.get_id()}'"
            )

        blocking_trade_ids = c.failed_trades_manager.get_blocking_trade_ids(
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
            raise IllegalArgumentException(
                f"intended trade amount {Coin.value_of(intended_trade_amount).to_plain_string().lower()} "
                f"is outside offer's min - max amount range of "
                f"{offer.min_amount.to_plain_string().lower()} - {offer.amount.to_plain_string().lower()}"
            )
