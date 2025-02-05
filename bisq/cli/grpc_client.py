from typing import Union
from bisq.cli.cli_methods import CliMethods
from bisq.cli.grpc_stubs import GrpcStubs
from bisq.cli.request.offers_service_request import OffersServiceRequest
from bisq.cli.request.payment_accounts_service_request import (
    PaymentAccountsServiceRequest,
)
from bisq.cli.request.trades_service_request import TradesServiceRequest
from bisq.cli.request.wallets_service_request import WalletsServiceRequest
import grpc_pb2


class GrpcClient:

    def __init__(self, api_host: str, api_port: int, api_password: str):
        self.grpc_stubs = GrpcStubs(api_host, api_port, api_password)
        self.offers_service_request = OffersServiceRequest(self.grpc_stubs)
        self.trades_service_request = TradesServiceRequest(self.grpc_stubs)
        self.wallets_service_request = WalletsServiceRequest(self.grpc_stubs)
        self.payment_accounts_service_request = PaymentAccountsServiceRequest(
            self.grpc_stubs
        )

    def close(self):
        self.grpc_stubs.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_version(self):
        request = grpc_pb2.GetVersionRequest()
        response: grpc_pb2.GetVersionReply = self.grpc_stubs.version_service.GetVersion(
            request
        )
        return response.version

    def get_network(self):
        return self.wallets_service_request.get_network()

    def get_dao_status(self):
        return self.wallets_service_request.get_dao_status()

    def get_balances(self, currency_code: str = ""):
        return self.wallets_service_request.get_balances(currency_code)

    def get_bsq_balances(self):
        return self.wallets_service_request.get_bsq_balances()

    def get_btc_balances(self):
        return self.wallets_service_request.get_btc_balances()

    def get_address_balance(self, address: str):
        return self.wallets_service_request.get_address_balance(address)

    def get_average_bsq_trade_price(self, days: int) -> grpc_pb2.AverageBsqTradePrice:
        request = grpc_pb2.GetAverageBsqTradePriceRequest(days=days)
        response: grpc_pb2.GetAverageBsqTradePriceReply = (
            self.grpc_stubs.price_service.GetAverageBsqTradePrice(request)
        )
        return response.price

    def get_btc_price(self, currency_code: str):
        return self.wallets_service_request.get_btc_price(currency_code)

    def get_funding_addresses(self):
        return self.wallets_service_request.get_funding_addresses()

    def get_unused_bsq_address(self):
        return self.wallets_service_request.get_unused_bsq_address()

    def get_unused_btc_address(self):
        return self.wallets_service_request.get_unused_btc_address()

    def send_bsq(self, address: str, amount: str, tx_fee_rate: str):
        return self.wallets_service_request.send_bsq(address, amount, tx_fee_rate)

    def send_btc(self, address: str, amount: str, tx_fee_rate: str, memo: str):
        return self.wallets_service_request.send_btc(address, amount, tx_fee_rate, memo)

    def verify_bsq_sent_to_address(self, address: str, amount: str):
        return self.wallets_service_request.verify_bsq_sent_to_address(address, amount)

    def get_tx_fee_rate(self):
        return self.wallets_service_request.get_tx_fee_rate()

    def set_tx_fee_rate(self, tx_fee_rate: int):
        return self.wallets_service_request.set_tx_fee_rate(tx_fee_rate)

    def unset_tx_fee_rate(self):
        return self.wallets_service_request.unset_tx_fee_rate()

    def get_transactions(self):
        return self.wallets_service_request.get_transactions()

    def get_transaction(self, tx_id: str):
        return self.wallets_service_request.get_transaction(tx_id)

    def get_available_offer_category(self, offer_id: str):
        return self.offers_service_request.get_available_offer_category(offer_id)

    def get_my_offer_category(self, offer_id: str):
        return self.offers_service_request.get_my_offer_category(offer_id)

    def create_bsq_swap_offer(
        self, direction: str, amount: int, min_amount: int, fixed_price: str
    ):
        return self.offers_service_request.create_bsq_swap_offer(
            direction, amount, min_amount, fixed_price
        )

    def create_fixed_priced_offer(
        self,
        direction: str,
        currency_code: str,
        amount: int,
        min_amount: int,
        fixed_price: str,
        security_deposit_pct: float,
        payment_acct_id: str,
        maker_fee_currency_code: str,
    ):
        return self.offers_service_request.create_offer(
            direction,
            currency_code,
            amount,
            min_amount,
            False,
            fixed_price,
            0.00,
            security_deposit_pct,
            payment_acct_id,
            maker_fee_currency_code,
            "0",  # no trigger price
        )

    def create_market_based_priced_offer(
        self,
        direction: str,
        currency_code: str,
        amount: int,
        min_amount: int,
        market_price_margin_pct: float,
        security_deposit_pct: float,
        payment_acct_id: str,
        maker_fee_currency_code: str,
        trigger_price: str,
    ):
        return self.offers_service_request.create_offer(
            direction,
            currency_code,
            amount,
            min_amount,
            True,
            "0",
            market_price_margin_pct,
            security_deposit_pct,
            payment_acct_id,
            maker_fee_currency_code,
            trigger_price,
        )

    def create_offer(
        self,
        direction: str,
        currency_code: str,
        amount: int,
        min_amount: int,
        use_market_based_price: bool,
        fixed_price: str,
        market_price_margin_pct: float,
        security_deposit_pct: float,
        payment_acct_id: str,
        maker_fee_currency_code: str,
        trigger_price: str,
    ):
        return self.offers_service_request.create_offer(
            direction,
            currency_code,
            amount,
            min_amount,
            use_market_based_price,
            fixed_price,
            market_price_margin_pct,
            security_deposit_pct,
            payment_acct_id,
            maker_fee_currency_code,
            trigger_price,
        )

    def edit_offer_activation_state(self, offer_id: str, enable: int):
        return self.offers_service_request.edit_offer_activation_state(offer_id, enable)

    def edit_offer_fixed_price(self, offer_id: str, price_as_string: str):
        return self.offers_service_request.edit_offer_fixed_price(
            offer_id, price_as_string
        )

    def edit_offer_price_margin(self, offer_id: str, market_price_margin: float):
        return self.offers_service_request.edit_offer_price_margin(
            offer_id, market_price_margin
        )

    def edit_offer_trigger_price(self, offer_id: str, trigger_price: str):
        return self.offers_service_request.edit_offer_trigger_price(
            offer_id, trigger_price
        )

    def edit_offer(
        self,
        offer_id: str,
        price: str,
        use_market_based_price: bool,
        market_price_margin_pct: float,
        trigger_price: str,
        enable: int,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ):
        # Take care when using this method directly:
        #  useMarketBasedPrice = true if margin based offer, false for fixed priced offer
        #  scaledPriceString fmt = ######.####
        return self.offers_service_request.edit_offer(
            offer_id,
            price,
            use_market_based_price,
            market_price_margin_pct,
            trigger_price,
            enable,
            edit_type,
        )

    def cancel_offer(self, offer_id: str):
        return self.offers_service_request.cancel_offer(offer_id)

    def get_bsq_swap_offer(self, offer_id: str):
        return self.offers_service_request.get_bsq_swap_offer(offer_id)

    def get_offer(self, offer_id: str):
        return self.offers_service_request.get_offer(offer_id)

    def get_my_offer(self, offer_id: str):
        print("get_my_offer deprecated Since 5-Dec-2021.")
        print(
            "Endpoint to be removed from future version. Use get_offer service method instead."
        )
        return self.offers_service_request.get_my_offer(offer_id)

    def get_bsq_swap_offers(self, direction: str):
        return self.offers_service_request.get_bsq_swap_offers(direction)

    def get_offers(self, direction: str, currency_code: str, all: bool):
        return self.offers_service_request.get_offers(direction, currency_code, all)

    def get_offers_sorted_by_date(
        self, currency_code: str, all: bool, direction: str = None
    ):
        return self.offers_service_request.get_offers_sorted_by_date(
            currency_code, all, direction
        )

    def get_bsq_swap_offers_sorted_by_date(self):
        return self.offers_service_request.get_bsq_swap_offers_sorted_by_date()

    def get_my_offers(self, direction: str, currency_code: str):
        return self.offers_service_request.get_my_offers(direction, currency_code)

    def get_my_offers_sorted_by_date(self, currency_code: str, direction: str = None):
        return self.offers_service_request.get_my_offers_sorted_by_date(
            currency_code, direction
        )

    def get_my_bsq_swap_offers_sorted_by_date(self):
        return self.offers_service_request.get_my_bsq_swap_offers_sorted_by_date()

    def take_bsq_swap_offer(self, offer_id: str, amount: int):
        return self.trades_service_request.take_bsq_swap_offer(offer_id, amount)

    def take_offer(
        self,
        offer_id: str,
        payment_account_id: str,
        taker_fee_currency_code: str,
        amount: int,
    ):
        return self.trades_service_request.take_offer(
            offer_id, payment_account_id, taker_fee_currency_code, amount
        )

    def get_trade(self, trade_id: str):
        return self.trades_service_request.get_trade(trade_id)

    def get_open_trades(self):
        return self.trades_service_request.get_open_trades()

    def get_trade_history(self, category: grpc_pb2.GetTradesRequest.Category):
        return self.trades_service_request.get_trade_history(category)

    def confirm_payment_started(self, trade_id: str):
        return self.trades_service_request.confirm_payment_started(trade_id)

    def confirm_payment_started_xmr(self, trade_id: str, tx_id: str, tx_key: str):
        return self.trades_service_request.confirm_payment_started_xmr(
            trade_id, tx_id, tx_key
        )

    def confirm_payment_received(self, trade_id: str):
        return self.trades_service_request.confirm_payment_received(trade_id)

    def close_trade(self, trade_id: str):
        return self.trades_service_request.close_trade(trade_id)

    def withdraw_funds(self, trade_id: str, address: str, memo: str):
        return self.trades_service_request.withdraw_funds(trade_id, address, memo)

    def fail_trade(self, trade_id: str):
        return self.trades_service_request.fail_trade(trade_id)

    def unfail_trade(self, trade_id: str):
        return self.trades_service_request.unfail_trade(trade_id)

    def get_payment_methods(self):
        return self.payment_accounts_service_request.get_payment_methods()

    def get_payment_account_form_as_json(self, payment_method_id: str):
        return self.payment_accounts_service_request.get_payment_account_form_as_json(
            payment_method_id
        )

    def create_payment_account(self, json: str):
        return self.payment_accounts_service_request.create_payment_account(json)

    def get_payment_accounts(self):
        return self.payment_accounts_service_request.get_payment_accounts()

    def get_payment_account(self, account_name: str):
        return self.payment_accounts_service_request.get_payment_account(account_name)

    def create_crypto_currency_payment_account(
        self, account_name: str, currency_code: str, address: str, trade_instant: bool
    ):
        return self.payment_accounts_service_request.create_crypto_currency_payment_account(
            account_name, currency_code, address, trade_instant
        )

    def get_crypto_payment_methods(self):
        return self.payment_accounts_service_request.get_crypto_payment_methods()

    def lock_wallet(self):
        return self.wallets_service_request.lock_wallet()

    def unlock_wallet(self, wallet_password: str, timeout: int):
        return self.wallets_service_request.unlock_wallet(wallet_password, timeout)

    def remove_wallet_password(self, wallet_password: str):
        return self.wallets_service_request.remove_wallet_password(wallet_password)

    def set_wallet_password(
        self, wallet_password: str, new_wallet_password: str = None
    ):
        return self.wallets_service_request.set_wallet_password(
            wallet_password, new_wallet_password=None
        )

    def register_dispute_agent(self, dispute_agent_type: str, registration_key: str):
        request = grpc_pb2.RegisterDisputeAgentRequest(
            dispute_agent_type=dispute_agent_type, registration_key=registration_key
        )
        response: grpc_pb2.RegisterDisputeAgentReply = (
            self.grpc_stubs.dispute_agents_service.RegisterDisputeAgent(request)
        )
        return response

    def stop_server(self):
        request = grpc_pb2.StopRequest()
        response: grpc_pb2.StopReply = self.grpc_stubs.shutdown_service.Stop(request)
        return response

    def get_method_help(self, method: Union[CliMethods, str]):
        if isinstance(method, CliMethods):
            method = method.name
        request = grpc_pb2.GetMethodHelpRequest(method_name=method)
        response: grpc_pb2.GetMethodHelpReply = (
            self.grpc_stubs.help_service.GetMethodHelp(request)
        )
        return response.method_help
