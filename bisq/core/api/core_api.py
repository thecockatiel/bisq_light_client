from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_logger
from bisq.common.version import Version
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2


if TYPE_CHECKING:
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
    from bisq.core.api.core_dipsute_agents_service import CoreDisputeAgentsService
    from bisq.core.api.core_help_service import CoreHelpService
    from bisq.core.api.core_offers_service import CoreOffersService
    from bisq.core.api.core_payment_accounts_service import CorePaymentAccountsService
    from bisq.core.api.core_price_service import CorePriceService
    from bisq.core.api.core_trades_service import CoreTradesService
    from bisq.core.api.core_wallets_service import CoreWalletsService
    from bisq.core.trade.statistics.trade_statistics_manager import (
        TradeStatisticsManager,
    )

logger = get_logger(__name__)


class CoreApi:

    def __init__(
        self,
        config: "Config",
        core_dispute_agents_service: "CoreDisputeAgentsService",
        core_help_service: "CoreHelpService",
        core_offers_service: "CoreOffersService",
        payment_accounts_service: "CorePaymentAccountsService",
        core_price_service: "CorePriceService",
        core_trades_service: "CoreTradesService",
        wallets_service: "CoreWalletsService",
        trade_statistics_manager: "TradeStatisticsManager",
        network_node: "NetworkNode",
    ):
        self.config = config
        self.core_dispute_agents_service = core_dispute_agents_service
        self.core_help_service = core_help_service
        self.core_offers_service = core_offers_service
        self.payment_accounts_service = payment_accounts_service
        self.core_price_service = core_price_service
        self.core_trades_service = core_trades_service
        self.wallets_service = wallets_service
        self.trade_statistics_manager = trade_statistics_manager
        self.network_node = network_node

    def get_version(self) -> str:
        return Version.VERSION

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Dispute Agents
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def register_dispute_agent(
        self, dispute_agent_type: str, registration_key: str
    ) -> None:
        self.core_dispute_agents_service.register_dispute_agent(
            dispute_agent_type, registration_key
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Help
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_method_help(self, method_name: str) -> str:
        return self.core_help_service.get_method_help(method_name)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Offers
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_fiat_offer(self, offer_id: str, is_my_offer: bool) -> bool:
        return self.core_offers_service.is_fiat_offer(offer_id, is_my_offer)

    def is_altcoin_offer(self, offer_id: str, is_my_offer: bool) -> bool:
        return self.core_offers_service.is_altcoin_offer(offer_id, is_my_offer)

    def is_bsq_swap_offer(self, offer_id: str, is_my_offer: bool) -> bool:
        return self.core_offers_service.is_bsq_swap_offer(offer_id, is_my_offer)

    def get_bsq_swap_offer(self, offer_id: str) -> "Offer":
        return self.core_offers_service.get_bsq_swap_offer(offer_id)

    def get_offer(self, offer_id: str) -> "Offer":
        return self.core_offers_service.get_offer(offer_id)

    def find_available_offer(self, offer_id: str) -> "Optional[Offer]":
        return self.core_offers_service.find_available_offer(offer_id)

    def get_my_offer(self, offer_id: str) -> "OpenOffer":
        return self.core_offers_service.get_my_offer(offer_id)

    def find_my_open_offer(self, offer_id: str) -> "Optional[OpenOffer]":
        return self.core_offers_service.find_my_open_offer(offer_id)

    def get_my_bsq_swap_offer(self, offer_id: str) -> "Offer":
        return self.core_offers_service.get_my_bsq_swap_offer(offer_id)

    def get_bsq_swap_offers(self, direction: str) -> "list[Offer]":
        return self.core_offers_service.get_bsq_swap_offers(direction)

    def get_offers(
        self, direction: str, currency_code: str
    ) -> "list[Offer]":
        return self.core_offers_service.get_offers(direction, currency_code)

    def get_my_offers(self, direction: str, currency_code: str) -> "list[OpenOffer]":
        return self.core_offers_service.get_my_offers(direction, currency_code)

    def get_my_bsq_swap_offers(self, direction: str) -> "list[Offer]":
        return self.core_offers_service.get_my_bsq_swap_offers(direction)

    def get_my_open_bsq_swap_offer(self, offer_id: str) -> "OpenOffer":
        return self.core_offers_service.get_my_open_bsq_swap_offer(offer_id)

    def create_and_place_bsq_swap_offer(
        self,
        direction: str,
        amount: int,
        min_amount: int,
        price: str,
        result_handler: Callable[["Offer"], None],
    ) -> None:
        self.core_offers_service.create_and_place_bsq_swap_offer(
            direction, amount, min_amount, price, result_handler
        )

    def create_and_place_offer(
        self,
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
        self.core_offers_service.create_and_place_offer(
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
        offer_id: str,
        price: str,
        use_market_based_price: bool,
        market_price_margin: float,
        trigger_price: str,
        enable: int,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ) -> None:
        self.core_offers_service.edit_offer(
            offer_id,
            price,
            use_market_based_price,
            market_price_margin,
            trigger_price,
            enable,
            edit_type,
        )

    def cancel_offer(self, offer_id: str) -> None:
        self.core_offers_service.cancel_offer(offer_id)

    def is_my_offer(self, offer: "Offer") -> bool:
        return self.core_offers_service.is_my_offer(offer)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PaymentAccounts
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_payment_account(self, json_string: str) -> "PaymentAccount":
        return self.payment_accounts_service.create_payment_account(json_string)

    def get_payment_accounts(self) -> "set[PaymentAccount]":
        return self.payment_accounts_service.get_payment_accounts()

    def get_fiat_payment_methods(self) -> "list[PaymentMethod]":
        return self.payment_accounts_service.get_fiat_payment_methods()

    def get_payment_account_form(self, payment_method_id: str) -> str:
        return self.payment_accounts_service.get_payment_account_form_as_string(
            payment_method_id
        )

    def create_crypto_currency_payment_account(
        self, account_name: str, currency_code: str, address: str, trade_instant: bool
    ) -> "PaymentAccount":
        return self.payment_accounts_service.create_crypto_currency_payment_account(
            account_name, currency_code, address, trade_instant
        )

    def get_crypto_currency_payment_methods(self) -> "list[PaymentMethod]":
        return self.payment_accounts_service.get_crypto_currency_payment_methods()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Prices
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_market_price(
        self, currency_code: str, result_handler: Callable[[float], None]
    ) -> None:
        self.core_price_service.get_market_price(currency_code, result_handler)

    def get_average_bsq_trade_price(self, days: int) -> tuple:
        return self.core_price_service.get_average_bsq_trade_price(days)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Trades
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def take_bsq_swap_offer(
        self,
        offer_id: str,
        intended_trade_amount: int,
        trade_result_handler: "TradeResultHandler[BsqSwapTrade]",
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        bsq_swap_offer = self.core_offers_service.get_bsq_swap_offer(offer_id)
        self.core_trades_service.take_bsq_swap_offer(
            bsq_swap_offer,
            intended_trade_amount,
            trade_result_handler,
            error_message_handler,
        )

    def take_offer(
        self,
        offer_id: str,
        payment_account_id: str,
        taker_fee_currency_code: str,
        intended_trade_amount: int,
        result_handler: Callable[["Trade"], None],
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        offer = self.core_offers_service.get_offer(offer_id)
        self.core_trades_service.take_offer(
            offer,
            payment_account_id,
            taker_fee_currency_code,
            intended_trade_amount,
            result_handler,
            error_message_handler,
        )

    def confirm_payment_started(
        self, trade_id: str, tx_id: Optional[str] = None, tx_key: Optional[str] = None
    ) -> None:
        self.core_trades_service.confirm_payment_started(trade_id, tx_id, tx_key)

    def confirm_payment_received(self, trade_id: str) -> None:
        self.core_trades_service.confirm_payment_received(trade_id)

    def close_trade(self, trade_id: str) -> None:
        self.core_trades_service.close_trade(trade_id)

    def withdraw_funds(self, trade_id: str, address: str, memo: str) -> None:
        self.core_trades_service.withdraw_funds(trade_id, address, memo)

    def get_trade_model(self, trade_id: str) -> "TradeModel":
        return self.core_trades_service.get_trade_model(trade_id)

    def get_open_trades(self) -> "list[TradeModel]":
        return self.core_trades_service.get_open_trades()

    def get_trade_history(
        self, category: grpc_pb2.GetTradesRequest.Category
    ) -> "list[TradeModel]":
        return self.core_trades_service.get_trade_history(category)

    def get_trade_role(self, trade_model: "TradeModel") -> str:
        return self.core_trades_service.get_trade_role(trade_model)

    def fail_trade(self, trade_id: str) -> None:
        self.core_trades_service.fail_trade(trade_id)

    def unfail_trade(self, trade_id: str) -> None:
        self.core_trades_service.unfail_trade(trade_id)

    def get_canceled_open_offers(self) -> "list[OpenOffer]":
        return self.core_trades_service.get_canceled_open_offers()

    def get_closed_trade_state_as_string(self, tradable: "Tradable") -> str:
        return self.core_trades_service.get_closed_trade_state_as_string(tradable)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Wallets
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_network_name(self) -> str:
        return self.wallets_service.get_network_name()

    @property
    def is_dao_state_ready_and_in_sync(self):
        return self.wallets_service.is_dao_state_ready_and_in_sync

    def get_balances(self, currency_code: str) -> "BalancesInfo":
        return self.wallets_service.get_balances(currency_code)

    def get_address_balance(self, address_string: str) -> int:
        return self.wallets_service.get_address_balance(address_string)

    def get_address_balance_info(self, address_string: str) -> "AddressBalanceInfo":
        return self.wallets_service.get_address_balance_info(address_string)

    def get_funding_addresses(self) -> "list[AddressBalanceInfo]":
        return self.wallets_service.get_funding_addresses()

    def get_unused_bsq_address(self) -> str:
        return self.wallets_service.get_unused_bsq_address()

    def send_bsq(
        self,
        address: str,
        amount: str,
        tx_fee_rate: str,
        callback: "TxBroadcasterCallback",
    ) -> None:
        self.wallets_service.send_bsq(address, amount, tx_fee_rate, callback)

    def send_btc(
        self,
        address: str,
        amount: str,
        tx_fee_rate: str,
        memo: str,
        callback: "TxBroadcasterCallback",
    ) -> None:
        self.wallets_service.send_btc(address, amount, tx_fee_rate, memo, callback)

    def verify_bsq_sent_to_address(self, address: str, amount: str) -> bool:
        return self.wallets_service.verify_bsq_sent_to_address(address, amount)

    def set_tx_fee_rate_preference(self, tx_fee_rate: int) -> None:
        self.wallets_service.set_tx_fee_rate_preference(tx_fee_rate)

    def unset_tx_fee_rate_preference(self) -> None:
        self.wallets_service.unset_tx_fee_rate_preference()

    def get_most_recent_tx_fee_rate_info(self) -> "TxFeeRateInfo":
        return self.wallets_service.get_most_recent_tx_fee_rate_info()

    def get_transactions(self) -> "set[Transaction]":
        return self.wallets_service.get_transactions()

    def get_transaction(self, tx_id: str) -> "Transaction":
        return self.wallets_service.get_transaction(tx_id)

    def get_transaction_confirmations(self, tx_id: str) -> int:
        return self.wallets_service.get_transaction_confirmations(tx_id)

    def set_wallet_password(self, password: str, new_password: str) -> None:
        self.wallets_service.set_wallet_password(password, new_password)

    def lock_wallet(self) -> None:
        self.wallets_service.lock_wallet()

    def unlock_wallet(self, password: str, timeout: int) -> None:
        self.wallets_service.unlock_wallet(password, timeout)

    def remove_wallet_password(self, password: str) -> None:
        self.wallets_service.remove_wallet_password(password)

    def get_num_confirmations_for_most_recent_transaction(
        self, address_string: str
    ) -> int:
        return self.wallets_service.get_num_confirmations_for_most_recent_transaction(
            address_string
        )

    def send_network_envelope(
        self, node_address: "NodeAddress", envelope: "NetworkEnvelope"
    ):
        if not self.config.use_dev_commands:
            raise IllegalStateException(
                "send_network_envelope is only available when useDevCommands is true"
            )
        return self.network_node.send_message(node_address, envelope)
