from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

from bisq.common.version import Version
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.user.user_context import UserContext
from grpc_extra_pb2 import BriefUserInfo
import grpc_pb2
from utils.aio import as_future


if TYPE_CHECKING:
    from shared_container import SharedContainer
    from bisq.common.protocol.network.network_envelope import NetworkEnvelope
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.api.model.tx_fee_rate_info import TxFeeRateInfo
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
    from bisq.core.trade.bisq_v1.trade_result_handler import TradeResultHandler
    from bitcoinj.core.transaction import Transaction
    from bisq.core.api.model.address_balance_info import AddressBalanceInfo
    from bisq.core.api.model.balances_info import BalancesInfo
    from bisq.core.trade.model.tradable import Tradable
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
    from bisq.core.payment.payload.payment_method import PaymentMethod
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.offer.offer import Offer
    from bisq.core.offer.open_offer import OpenOffer
    from bisq.common.config.config import Config
    from bisq.core.user.user_manager import UserManager
    from bisq.core.api.core_dipsute_agents_service import CoreDisputeAgentsService
    from bisq.core.api.core_help_service import CoreHelpService
    from bisq.core.api.core_offers_service import CoreOffersService
    from bisq.core.api.core_payment_accounts_service import CorePaymentAccountsService
    from bisq.core.api.core_price_service import CorePriceService
    from bisq.core.api.core_trades_service import CoreTradesService
    from bisq.core.api.core_wallets_service import CoreWalletsService


class CoreApi:

    def __init__(
        self,
        config: "Config",
        user_manager: "UserManager",
        shared_container: "SharedContainer",
        core_dispute_agents_service: "CoreDisputeAgentsService",
        core_help_service: "CoreHelpService",
        core_offers_service: "CoreOffersService",
        payment_accounts_service: "CorePaymentAccountsService",
        core_price_service: "CorePriceService",
        core_trades_service: "CoreTradesService",
        wallets_service: "CoreWalletsService",
    ):
        self._config = config
        self._user_manager = user_manager
        self._shared_container = shared_container
        self._core_dispute_agents_service = core_dispute_agents_service
        self._core_help_service = core_help_service
        self._core_offers_service = core_offers_service
        self._payment_accounts_service = payment_accounts_service
        self._core_price_service = core_price_service
        self._core_trades_service = core_trades_service
        self._wallets_service = wallets_service

    def get_version(self) -> str:
        return Version.VERSION + "p"

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Dispute Agents
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def register_dispute_agent(
        self,
        user_context: "UserContext",
        dispute_agent_type: str,
        registration_key: str,
    ) -> None:
        self._core_dispute_agents_service.register_dispute_agent(
            user_context, dispute_agent_type, registration_key
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Help
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_method_help(self, method_name: str) -> str:
        return self._core_help_service.get_method_help(method_name)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Offers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_fiat_offer(
        self, user_context: "UserContext", offer_id: str, is_my_offer: bool
    ) -> bool:
        return self._core_offers_service.is_fiat_offer(
            user_context, offer_id, is_my_offer
        )

    def is_altcoin_offer(
        self, user_context: "UserContext", offer_id: str, is_my_offer: bool
    ) -> bool:
        return self._core_offers_service.is_altcoin_offer(
            user_context, offer_id, is_my_offer
        )

    def is_bsq_swap_offer(
        self, user_context: "UserContext", offer_id: str, is_my_offer: bool
    ) -> bool:
        return self._core_offers_service.is_bsq_swap_offer(
            user_context, offer_id, is_my_offer
        )

    def get_bsq_swap_offer(self, user_context: "UserContext", offer_id: str) -> "Offer":
        return self._core_offers_service.get_bsq_swap_offer(user_context, offer_id)

    def get_offer(self, user_context: "UserContext", offer_id: str) -> "Offer":
        return self._core_offers_service.get_offer(user_context, offer_id)

    def find_available_offer(
        self, user_context: "UserContext", offer_id: str
    ) -> "Optional[Offer]":
        return self._core_offers_service.find_available_offer(user_context, offer_id)

    def get_my_offer(self, user_context: "UserContext", offer_id: str) -> "OpenOffer":
        return self._core_offers_service.get_my_offer(user_context, offer_id)

    def find_my_open_offer(
        self, user_context: "UserContext", offer_id: str
    ) -> "Optional[OpenOffer]":
        return self._core_offers_service.find_my_open_offer(user_context, offer_id)

    def get_my_bsq_swap_offer(
        self, user_context: "UserContext", offer_id: str
    ) -> "Offer":
        return self._core_offers_service.get_my_bsq_swap_offer(user_context, offer_id)

    def get_bsq_swap_offers(
        self, user_context: "UserContext", direction: str
    ) -> "list[Offer]":
        return self._core_offers_service.get_bsq_swap_offers(user_context, direction)

    def get_offers(
        self, user_context: "UserContext", direction: str, currency_code: str
    ) -> "list[Offer]":
        return self._core_offers_service.get_offers(
            user_context, direction, currency_code
        )

    def get_my_offers(
        self, user_context: "UserContext", direction: str, currency_code: str
    ) -> "list[OpenOffer]":
        return self._core_offers_service.get_my_offers(
            user_context, direction, currency_code
        )

    def get_my_bsq_swap_offers(
        self, user_context: "UserContext", direction: str
    ) -> "list[Offer]":
        return self._core_offers_service.get_my_bsq_swap_offers(user_context, direction)

    def get_my_open_bsq_swap_offer(
        self, user_context: "UserContext", offer_id: str
    ) -> "OpenOffer":
        return self._core_offers_service.get_my_open_bsq_swap_offer(
            user_context, offer_id
        )

    def create_and_place_bsq_swap_offer(
        self,
        user_context: "UserContext",
        direction: str,
        amount: int,
        min_amount: int,
        price: str,
        result_handler: Callable[["Offer"], None],
    ) -> None:
        self._core_offers_service.create_and_place_bsq_swap_offer(
            user_context, direction, amount, min_amount, price, result_handler
        )

    def create_and_place_offer(
        self,
        user_context: "UserContext",
        currency_code: str,
        direction: str,
        price: str,
        use_market_based_price: bool,
        market_price_margin: float,
        amount: int,
        min_amount: int,
        buyer_security_deposit_pct: float,
        trigger_price: str,
        payment_account_id: str,
        maker_fee_currency_code: str,
        result_handler: Callable[["Offer"], None],
    ) -> None:
        self._core_offers_service.create_and_place_offer(
            user_context,
            currency_code,
            direction,
            price if not use_market_based_price else "0",
            use_market_based_price,
            market_price_margin,
            amount,
            min_amount,
            buyer_security_deposit_pct,
            trigger_price,
            payment_account_id,
            maker_fee_currency_code,
            result_handler,
        )

    def edit_offer(
        self,
        user_context: "UserContext",
        offer_id: str,
        price: str,
        use_market_based_price: bool,
        market_price_margin: float,
        trigger_price: str,
        enable: int,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ) -> None:
        self._core_offers_service.edit_offer(
            user_context,
            offer_id,
            price,
            use_market_based_price,
            market_price_margin,
            trigger_price,
            enable,
            edit_type,
        )

    def cancel_offer(self, user_context: "UserContext", offer_id: str) -> None:
        self._core_offers_service.cancel_offer(user_context, offer_id)

    def is_my_offer(self, user_context: "UserContext", offer: "Offer") -> bool:
        return self._core_offers_service.is_my_offer(user_context, offer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PaymentAccounts
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_payment_account(
        self,
        user_context: "UserContext",
        json_string: str,
    ) -> "PaymentAccount":
        return self._payment_accounts_service.create_payment_account(
            user_context,
            json_string,
        )

    def get_payment_accounts(
        self,
        user_context: "UserContext",
    ) -> "set[PaymentAccount]":
        return self._payment_accounts_service.get_payment_accounts(user_context)

    def get_fiat_payment_methods(self) -> "list[PaymentMethod]":
        return self._payment_accounts_service.get_fiat_payment_methods()

    def get_payment_account_form(self, payment_method_id: str) -> str:
        return self._payment_accounts_service.get_payment_account_form_as_string(
            payment_method_id
        )

    def create_crypto_currency_payment_account(
        self,
        user_context: "UserContext",
        account_name: str,
        currency_code: str,
        address: str,
        trade_instant: bool,
    ) -> "PaymentAccount":
        return self._payment_accounts_service.create_crypto_currency_payment_account(
            user_context,
            account_name,
            currency_code,
            address,
            trade_instant,
        )

    def get_crypto_currency_payment_methods(self) -> "list[PaymentMethod]":
        return self._payment_accounts_service.get_crypto_currency_payment_methods()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Prices
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_market_price(
        self,
        user_context: "UserContext",
        currency_code: str,
        result_handler: Callable[[float], None],
    ) -> None:
        self._core_price_service.get_market_price(
            user_context, currency_code, result_handler
        )

    def get_average_bsq_trade_price(
        self, user_context: "UserContext", days: int
    ) -> tuple:
        return self._core_price_service.get_average_bsq_trade_price(user_context, days)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Trades
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def take_bsq_swap_offer(
        self,
        user_context: "UserContext",
        offer_id: str,
        intended_trade_amount: int,
        trade_result_handler: "TradeResultHandler[BsqSwapTrade]",
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        bsq_swap_offer = self._core_offers_service.get_bsq_swap_offer(
            user_context, offer_id
        )
        self._core_trades_service.take_bsq_swap_offer(
            user_context,
            bsq_swap_offer,
            intended_trade_amount,
            trade_result_handler,
            error_message_handler,
        )

    def take_offer(
        self,
        user_context: "UserContext",
        offer_id: str,
        payment_account_id: str,
        taker_fee_currency_code: str,
        intended_trade_amount: int,
        result_handler: Callable[["Trade"], None],
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        offer = self._core_offers_service.get_offer(user_context, offer_id)
        self._core_trades_service.take_offer(
            user_context,
            offer,
            payment_account_id,
            taker_fee_currency_code,
            intended_trade_amount,
            result_handler,
            error_message_handler,
        )

    def confirm_payment_started(
        self,
        user_context: "UserContext",
        trade_id: str,
        tx_id: Optional[str] = None,
        tx_key: Optional[str] = None,
    ) -> None:
        self._core_trades_service.confirm_payment_started(
            user_context, trade_id, tx_id, tx_key
        )

    def confirm_payment_received(
        self, user_context: "UserContext", trade_id: str
    ) -> None:
        self._core_trades_service.confirm_payment_received(user_context, trade_id)

    def close_trade(self, user_context: "UserContext", trade_id: str) -> None:
        self._core_trades_service.close_trade(user_context, trade_id)

    def withdraw_funds(
        self, user_context: "UserContext", trade_id: str, address: str, memo: str
    ) -> None:
        self._core_trades_service.withdraw_funds(user_context, trade_id, address, memo)

    def get_trade_model(
        self, user_context: "UserContext", trade_id: str
    ) -> "TradeModel":
        return self._core_trades_service.get_trade_model(user_context, trade_id)

    def get_open_trades(self, user_context: "UserContext") -> "list[TradeModel]":
        return self._core_trades_service.get_open_trades(user_context)

    def get_trade_history(
        self, user_context: "UserContext", category: grpc_pb2.GetTradesRequest.Category
    ) -> "list[TradeModel]":
        return self._core_trades_service.get_trade_history(user_context, category)

    def get_trade_role(
        self, user_context: "UserContext", trade_model: "TradeModel"
    ) -> str:
        return self._core_trades_service.get_trade_role(user_context, trade_model)

    def fail_trade(self, user_context: "UserContext", trade_id: str) -> None:
        self._core_trades_service.fail_trade(user_context, trade_id)

    def unfail_trade(self, user_context: "UserContext", trade_id: str) -> None:
        self._core_trades_service.unfail_trade(user_context, trade_id)

    def get_canceled_open_offers(
        self, user_context: "UserContext"
    ) -> "list[OpenOffer]":
        return self._core_trades_service.get_canceled_open_offers(user_context)

    def get_closed_trade_state_as_string(
        self, user_context: "UserContext", tradable: "Tradable"
    ) -> str:
        return self._core_trades_service.get_closed_trade_state_as_string(
            user_context, tradable
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Wallets
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_network_name(self, user_context: "UserContext") -> str:
        return self._wallets_service.get_network_name(user_context)

    def is_dao_state_ready_and_in_sync(self, user_context: "UserContext"):
        return self._wallets_service.is_dao_state_ready_and_in_sync(user_context)

    def get_balances(
        self, user_context: "UserContext", currency_code: str
    ) -> "BalancesInfo":
        return self._wallets_service.get_balances(user_context, currency_code)

    def get_address_balance(
        self, user_context: "UserContext", address_string: str
    ) -> int:
        return self._wallets_service.get_address_balance(user_context, address_string)

    def get_address_balance_info(
        self, user_context: "UserContext", address_string: str
    ) -> "AddressBalanceInfo":
        return self._wallets_service.get_address_balance_info(
            user_context, address_string
        )

    def get_funding_addresses(
        self, user_context: "UserContext"
    ) -> "list[AddressBalanceInfo]":
        return self._wallets_service.get_funding_addresses(user_context)

    def get_unused_bsq_address(self, user_context: "UserContext") -> str:
        return self._wallets_service.get_unused_bsq_address(user_context)

    def send_bsq(
        self,
        user_context: "UserContext",
        address: str,
        amount: str,
        tx_fee_rate: str,
        callback: "TxBroadcasterCallback",
    ) -> None:
        self._wallets_service.send_bsq(
            user_context,
            address,
            amount,
            tx_fee_rate,
            callback,
        )

    def send_btc(
        self,
        user_context: "UserContext",
        address: str,
        amount: str,
        tx_fee_rate: str,
        memo: str,
        callback: "TxBroadcasterCallback",
    ) -> None:
        self._wallets_service.send_btc(
            user_context,
            address,
            amount,
            tx_fee_rate,
            memo,
            callback,
        )

    def verify_bsq_sent_to_address(
        self, user_context: "UserContext", address: str, amount: str
    ) -> bool:
        return self._wallets_service.verify_bsq_sent_to_address(
            user_context, address, amount
        )

    def set_tx_fee_rate_preference(
        self, user_context: "UserContext", tx_fee_rate: int
    ) -> None:
        self._wallets_service.set_tx_fee_rate_preference(user_context, tx_fee_rate)

    def unset_tx_fee_rate_preference(self, user_context: "UserContext") -> None:
        self._wallets_service.unset_tx_fee_rate_preference(user_context)

    def get_most_recent_tx_fee_rate_info(
        self, user_context: "UserContext"
    ) -> "TxFeeRateInfo":
        return self._wallets_service.get_most_recent_tx_fee_rate_info(user_context)

    def get_transactions(self, user_context: "UserContext") -> "set[Transaction]":
        return self._wallets_service.get_transactions(user_context)

    def get_transaction(self, user_context: "UserContext", tx_id: str) -> "Transaction":
        return self._wallets_service.get_transaction(user_context, tx_id)

    def get_transaction_confirmations(
        self, user_context: "UserContext", tx_id: str
    ) -> int:
        return self._wallets_service.get_transaction_confirmations(user_context, tx_id)

    def set_wallet_password(
        self, user_context: "UserContext", password: str, new_password: str
    ) -> None:
        self._wallets_service.set_wallet_password(user_context, password, new_password)

    def lock_wallet(self, user_context: "UserContext") -> None:
        self._wallets_service.lock_wallet(user_context)

    def unlock_wallet(
        self, user_context: "UserContext", password: str, timeout: int
    ) -> None:
        self._wallets_service.unlock_wallet(user_context, password, timeout)

    def remove_wallet_password(
        self, user_context: "UserContext", password: str
    ) -> None:
        self._wallets_service.remove_wallet_password(user_context, password)

    def get_num_confirmations_for_most_recent_transaction(
        self, user_context: "UserContext", address_string: str
    ) -> int:
        return self._wallets_service.get_num_confirmations_for_most_recent_transaction(
            user_context, address_string
        )

    def send_network_envelope(
        self,
        user_context: "UserContext",
        node_address: "NodeAddress",
        envelope: "NetworkEnvelope",
    ):
        if not self._config.use_dev_commands:
            raise IllegalStateException(
                "send_network_envelope is only available when useDevCommands is true"
            )
        return user_context.global_container.network_node.send_message(
            node_address, envelope
        )

    def switch_user(self, user_id: str):
        return as_future(
            self._user_manager.switch_user(user_id, self._shared_container)
        )

    def create_new_user(self):
        return as_future(self._user_manager.create_user())

    def delete_user(self, user_id: str, remove_user_data: bool = False):
        return as_future(
            self._user_manager.delete_user(
                user_id, remove_user_data, self._shared_container
            )
        )

    def set_user_alias(self, user_id: str, alias: str):
        self._user_manager.set_user_alias(user_id, alias)

    def get_users_list(self):
        return [
            BriefUserInfo(user_id=ctx.user_id, alias=ctx.alias)
            for ctx in self._user_manager.get_all_contexts()
        ]

    def restore_user(self, user_id: str):
        return as_future(self._user_manager.create_user(user_id))
