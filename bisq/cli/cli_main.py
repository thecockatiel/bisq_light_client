from collections import defaultdict
from pathlib import Path
import sys
import traceback
from typing import Any

import grpc

from bisq.cli.cli_methods import CliMethods
from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.grpc_client import GrpcClient
from bisq.cli.opts.argument_list import ArgumentList
from bisq.cli.opts.create_crypto_currency_payment_account_option_parser import (
    CreateCryptoCurrencyPaymentAccountOptionParser,
)
from bisq.cli.opts.create_offer_option_parser import CreateOfferOptionParser
from bisq.cli.opts.create_payment_account_option_parser import (
    CreatePaymentAccountOptionParser,
)
from bisq.cli.opts.edit_offer_option_parser import EditOfferOptionParser
from bisq.cli.opts.get_address_balance_option_parser import (
    GetAddressBalanceOptionParser,
)
from bisq.cli.opts.get_avg_bsq_price_option_parser import GetAvgBsqPriceOptionParser
from bisq.cli.opts.get_balance_option_parser import GetBalanceOptionParser
from bisq.cli.opts.get_btc_market_price_option_parser import (
    GetBTCMarketPriceOptionParser,
)
from bisq.cli.opts.get_offers_option_parser import GetOffersOptionParser
from bisq.cli.opts.get_payment_account_form_option_parser import (
    GetPaymentAccountFormOptionParser,
)
from bisq.cli.opts.get_trade_option_parser import GetTradeOptionParser
from bisq.cli.opts.get_trades_option_parser import GetTradesOptionParser
from bisq.cli.opts.get_transaction_option_parser import GetTransactionOptionParser
from bisq.cli.opts.offer_id_option_parser import OfferIdOptionParser
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.register_dispute_agent_option_parser import (
    RegisterDisputeAgentOptionParser,
)
from bisq.cli.opts.remove_wallet_password_option_parser import (
    RemoveWalletPasswordOptionParser,
)
from bisq.cli.opts.send_bsq_option_parser import SendBsqOptionParser
from bisq.cli.opts.send_btc_option_parser import SendBtcOptionParser
from bisq.cli.opts.send_proto_option_parser import SendProtoOptionParser
from bisq.cli.opts.set_tx_fee_rate_option_parser import SetTxFeeRateOptionParser
from bisq.cli.opts.set_wallet_password_option_parser import (
    SetWalletPasswordOptionParser,
)
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.cli.opts.take_bsq_swap_offer_option_parser import TakeBsqSwapOfferOptionParser
from bisq.cli.opts.take_offer_option_parser import TakeOfferOptionParser
from bisq.cli.opts.unlock_wallet_option_parser import UnlockWalletOptionParser
from bisq.cli.opts.verify_bsq_sent_to_address_option_parser import (
    VerifyBsqSentToAddressOptionParser,
)
from bisq.cli.opts.withdraw_funds_option_parser import WithdrawFundsOptionParser
from bisq.cli.table.builder.table_builder import TableBuilder
from bisq.cli.table.builder.table_type import TableType
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from grpc_pb2 import GetOfferCategoryReply, GetTradesRequest
from utils.argparse_ext import CustomArgumentParser, CustomHelpFormatter
from datetime import datetime


class CliMain:

    @staticmethod
    def main(args: list[str]):
        try:
            CliMain._run(args)
        except Exception as e:
            if (
                isinstance(e, grpc.RpcError)
                and e.args
                and hasattr(e.args[0], "details")
            ):
                message = e.args[0].details
            else:
                message = str(e)
            print(f"Error: {message}", file=sys.stderr)
            if not isinstance(
                e, (IllegalArgumentException, IllegalStateException, grpc.RpcError)
            ):
                traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def _run(args: list[str]):
        options = defaultdict[str, Any](lambda: None)

        parser = CliMain._get_parser()

        arguments = ArgumentList(args)
        cli_args = arguments.get_cli_arguments()
        method_args = arguments.get_method_arguments()

        opts_ns, non_option_args = parser.parse_known_args(cli_args)
        cli_opts = {
            key: value for key, value in vars(opts_ns).items() if value is not None
        }  # get only present options

        options.update(cli_opts)

        if not options[OptLabel.OPT_HELP] and not non_option_args:
            CliMain._print_help(parser, file=sys.stderr)
            raise IllegalArgumentException("no method specified")

        if options[OptLabel.OPT_HELP] and not non_option_args:
            CliMain._print_help(parser, file=sys.stdout)
            return

        host = options["host"]
        port = options["port"]
        password = options["password"]

        if not host:
            raise IllegalArgumentException("missing required 'host' option")
        if not port:
            raise IllegalArgumentException("missing required 'port' option")
        if not password:
            raise IllegalArgumentException("missing required 'password' option")

        method_name = non_option_args[0]

        try:
            method = CliMain._get_method_from_cmd(method_name)
        except:
            raise IllegalArgumentException(f"'{method_name}' is not a supported method")

        with GrpcClient(host, port, password) as client:
            # may cause double parse, but reduces code duplication
            if SimpleMethodOptionParser(method_args).parse().is_for_help():
                print(client.get_method_help(method))
                return
            if method == CliMethods.getversion:
                return print(client.get_version())
            elif method == CliMethods.getnetwork:
                return print(client.get_network())
            elif method == CliMethods.getdaostatus:
                return print(client.get_dao_status())
            elif method == CliMethods.getbalance:
                currency_code = (
                    GetBalanceOptionParser(method_args).parse().get_currency_code()
                )
                balances = client.get_balances(currency_code)
                currency_code = currency_code.upper()
                if currency_code == "BSQ":
                    TableBuilder(
                        TableType.BSQ_BALANCE_TBL, balances.bsq
                    ).build().print()
                elif currency_code == "BTC":
                    TableBuilder(
                        TableType.BTC_BALANCE_TBL, balances.btc
                    ).build().print()
                else:
                    print("BTC")
                    TableBuilder(
                        TableType.BTC_BALANCE_TBL, balances.btc
                    ).build().print()
                    print("BSQ")
                    TableBuilder(
                        TableType.BSQ_BALANCE_TBL, balances.bsq
                    ).build().print()
            elif method == CliMethods.getaddressbalance:
                opts = GetAddressBalanceOptionParser(method_args).parse()
                address = opts.get_address()
                address_balance = client.get_address_balance(address)
                TableBuilder(
                    TableType.ADDRESS_BALANCE_TBL, address_balance
                ).build().print()
            elif method == CliMethods.getavgbsqprice:
                opts = GetAvgBsqPriceOptionParser(method_args).parse()
                days = opts.get_days()
                price = client.get_average_bsq_trade_price(days)
                print(
                    f"avg {days} day btc price: {price.btc_price}    avg {days} day usd price: {price.usd_price}"
                )
            elif method == CliMethods.getbtcprice:
                opts = GetBTCMarketPriceOptionParser(method_args).parse()
                currency_code = opts.get_currency_code()
                price = client.get_btc_price(currency_code)
                print(CurrencyFormat.format_internal_fiat_price(price))
            elif method == CliMethods.getfundingaddresses:
                funding_addresses = client.get_funding_addresses()
                TableBuilder(
                    TableType.ADDRESS_BALANCE_TBL, funding_addresses
                ).build().print()
            elif method == CliMethods.getunusedbsqaddress:
                address = client.get_unused_bsq_address()
                print(address)
            elif method == CliMethods.sendbsq:
                opts = SendBsqOptionParser(method_args).parse()
                address = opts.get_address()
                amount = opts.get_amount()
                CliMain._verify_string_is_valid_float(OptLabel.OPT_AMOUNT, amount)

                tx_fee_rate = opts.get_fee_rate()
                if tx_fee_rate:
                    CliMain._verify_string_is_valid_long(
                        OptLabel.OPT_TX_FEE_RATE, tx_fee_rate
                    )

                tx_info = client.send_bsq(address, amount, tx_fee_rate)
                print(f"{amount} bsq sent to {address} in tx {tx_info.tx_id}")
            elif method == CliMethods.sendbtc:
                opts = SendBtcOptionParser(method_args).parse()
                address = opts.get_address()
                amount = opts.get_amount()
                CliMain._verify_string_is_valid_float(OptLabel.OPT_AMOUNT, amount)

                tx_fee_rate = opts.get_fee_rate()
                if tx_fee_rate:
                    CliMain._verify_string_is_valid_long(
                        OptLabel.OPT_TX_FEE_RATE, tx_fee_rate
                    )

                memo = opts.get_memo()
                tx_info = client.send_btc(address, amount, tx_fee_rate, memo)
                print(f"{amount} btc sent to {address} in tx {tx_info.tx_id}")
            elif method == CliMethods.verifybsqsenttoaddress:
                opts = VerifyBsqSentToAddressOptionParser(method_args).parse()
                address = opts.get_address()
                amount = opts.get_amount()
                CliMain._verify_string_is_valid_float(OptLabel.OPT_AMOUNT, amount)

                bsq_was_sent = client.verify_bsq_sent_to_address(address, amount)
                print(
                    f"{amount} bsq {'has been' if bsq_was_sent else 'has not been'} sent to address {address}"
                )
            elif method == CliMethods.gettxfeerate:
                tx_fee_rate = client.get_tx_fee_rate()
                print(CurrencyFormat.format_tx_fee_rate_info(tx_fee_rate))
            elif method == CliMethods.settxfeerate:
                opts = SetTxFeeRateOptionParser(method_args).parse()
                tx_fee_rate = client.set_tx_fee_rate(int(opts.get_fee_rate()))
                print(CurrencyFormat.format_tx_fee_rate_info(tx_fee_rate))
            elif method == CliMethods.unsettxfeerate:
                tx_fee_rate = client.unset_tx_fee_rate()
                print(CurrencyFormat.format_tx_fee_rate_info(tx_fee_rate))
            elif method == CliMethods.gettransactions:
                txs = client.get_transactions()
                TableBuilder(TableType.TRANSACTION_TBL, txs).build().print()
            elif method == CliMethods.gettransaction:
                opts = GetTransactionOptionParser(method_args).parse()
                tx_id = opts.get_tx_id()
                tx = client.get_transaction(tx_id)
                TableBuilder(TableType.TRANSACTION_TBL, tx).build().print()
            elif method == CliMethods.createoffer:
                opts = CreateOfferOptionParser(method_args).parse()
                is_swap = opts.get_is_swap()
                payment_acct_id = opts.get_payment_account_id()
                direction = opts.get_direction()
                currency_code = opts.get_currency_code()
                amount = CurrencyFormat.to_satoshis(opts.get_amount())
                min_amount = CurrencyFormat.to_satoshis(opts.get_min_amount())
                use_market_based_price = opts.is_using_mkt_price_margin()
                fixed_price = opts.get_fixed_price()
                market_price_margin_pct = opts.get_mkt_price_margin_pct()
                security_deposit_pct = (
                    0.00 if is_swap else opts.get_security_deposit_pct()
                )
                maker_fee_currency_code = opts.get_maker_fee_currency_code()
                trigger_price = (
                    "0"  # Cannot be defined until the new offer is added to book.
                )

                if is_swap:
                    offer = client.create_bsq_swap_offer(
                        direction, amount, min_amount, fixed_price
                    )
                else:
                    offer = client.create_offer(
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

                TableBuilder(TableType.OFFER_TBL, offer).build().print()
            elif method == CliMethods.editoffer:
                offer_id_opts = OfferIdOptionParser(method_args).parse()
                # What kind of offer is being edited? BSQ swaps cannot be edited.
                offer_id = offer_id_opts.get_offer_id()
                offer_category = client.get_my_offer_category(offer_id)
                if offer_category == GetOfferCategoryReply.OfferCategory.BSQ_SWAP:
                    raise IllegalStateException(
                        "bsq swap offers cannot be edited, but you may cancel them without forfeiting any funds"
                    )

                opts = EditOfferOptionParser(offer_id_opts.non_option_args).parse()
                fixed_price = opts.get_fixed_price()
                is_using_mkt_price_margin = opts.is_using_mkt_price_margin()
                market_price_margin_pct = opts.get_mkt_price_margin_pct()
                trigger_price = opts.get_trigger_price()
                enable = opts.get_enable_as_signed_int()
                edit_offer_type = opts.get_offer_edit_type()

                client.edit_offer(
                    offer_id,
                    fixed_price,
                    is_using_mkt_price_margin,
                    market_price_margin_pct,
                    trigger_price,
                    enable,
                    edit_offer_type,
                )
                print("offer has been edited")
            elif method == CliMethods.canceloffer:
                opts = OfferIdOptionParser(method_args).parse()
                offer_id = opts.get_offer_id()
                client.cancel_offer(offer_id)
                print("offer canceled and removed from offer book")
            elif method == CliMethods.getoffer:
                opts = OfferIdOptionParser(method_args).parse()
                offer_id = opts.get_offer_id()
                offer = client.get_offer(offer_id)
                TableBuilder(TableType.OFFER_TBL, offer).build().print()
            elif method == CliMethods.getmyoffer:
                opts = OfferIdOptionParser(method_args).parse()
                offer_id = opts.get_offer_id()
                offer = client.get_my_offer(offer_id)
                TableBuilder(TableType.OFFER_TBL, offer).build().print()
            elif method == CliMethods.getoffers:
                opts = GetOffersOptionParser(method_args).parse()
                direction = opts.get_direction()
                currency_code = opts.get_currency_code()
                all_offers = opts.get_all()
                offers = client.get_offers(direction, currency_code, all_offers)
                if not offers:
                    print(f"no {direction} {currency_code} offers found")
                else:
                    TableBuilder(TableType.OFFER_TBL, offers).build().print()
            elif method == CliMethods.getmyoffers:
                opts = GetOffersOptionParser(method_args).parse()
                direction = opts.get_direction()
                currency_code = opts.get_currency_code()
                offers = client.get_my_offers(direction, currency_code)
                if not offers:
                    print(f"no {direction} {currency_code} offers found")
                else:
                    TableBuilder(TableType.OFFER_TBL, offers).build().print()
            elif method == CliMethods.takeoffer:
                offer_id_opts = OfferIdOptionParser(method_args).parse()
                offer_id = offer_id_opts.get_offer_id()
                # We only send an 'offer-id' param when taking a BsqSwapOffer.
                # Find out what kind of offer is being taken before sending a
                # 'takeoffer' request.
                offer_category = client.get_available_offer_category(offer_id)
                if offer_category == GetOfferCategoryReply.OfferCategory.BSQ_SWAP:
                    opts = TakeBsqSwapOfferOptionParser(
                        offer_id_opts.non_option_args
                    ).parse()
                    amount = CurrencyFormat.to_satoshis(opts.get_amount())
                    trade = client.take_bsq_swap_offer(offer_id, amount)
                else:
                    opts = TakeOfferOptionParser(offer_id_opts.non_option_args).parse()
                    amount = CurrencyFormat.to_satoshis(opts.get_amount())
                    payment_account_id = opts.get_payment_account_id()
                    taker_fee_currency_code = opts.get_taker_fee_currency_code()
                    trade = client.take_offer(
                        offer_id, payment_account_id, taker_fee_currency_code, amount
                    )
                print(f"trade {trade.trade_id} successfully taken")
            elif method == CliMethods.gettrade:
                # JAVA TODO make short-id a valid argument?
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                show_contract = opts.get_show_contract()
                trade = client.get_trade(trade_id)
                if show_contract:
                    print(trade.contract_as_json)
                else:
                    TableBuilder(TableType.TRADE_DETAIL_TBL, trade).build().print()
            elif method == CliMethods.gettrades:
                opts = GetTradesOptionParser(method_args).parse()
                category = opts.get_category()
                category_name = opts.get_category_name()
                trades = (
                    client.get_open_trades()
                    if category == GetTradesRequest.Category.OPEN
                    else client.get_trade_history(category)
                )
                if not trades:
                    print(f"no {category_name} trades found")
                else:
                    table_type = (
                        TableType.OPEN_TRADES_TBL
                        if category == GetTradesRequest.Category.OPEN
                        else (
                            TableType.CLOSED_TRADES_TBL
                            if category == GetTradesRequest.Category.CLOSED
                            else TableType.FAILED_TRADES_TBL
                        )
                    )
                    TableBuilder(table_type, trades).build().print()
            elif method == CliMethods.confirmpaymentstarted:
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                client.confirm_payment_started(trade_id)
                print(f"trade {trade_id} payment started message sent")
            elif method == CliMethods.confirmpaymentstartedxmr:
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                tx_id = opts.get_tx_id()
                tx_key = opts.get_tx_key()
                client.confirm_payment_started_xmr(trade_id, tx_id, tx_key)
                print(f"trade {trade_id} payment started message sent")
            elif method == CliMethods.confirmpaymentreceived:
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                client.confirm_payment_received(trade_id)
                print(f"trade {trade_id} payment received message sent")
            elif method == CliMethods.closetrade:
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                client.close_trade(trade_id)
                print(f"trade {trade_id} is closed")
            elif method == CliMethods.withdrawfunds:
                opts = WithdrawFundsOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                address = opts.get_address()
                # Multi-word memos must be double-quoted.
                memo = opts.get_memo()
                client.withdraw_funds(trade_id, address, memo)
                print(f"trade {trade_id} funds sent to btc address {address}")
            elif method == CliMethods.getpaymentmethods:
                payment_methods = client.get_payment_methods()
                for method in payment_methods:
                    print(method.id)
            elif method == CliMethods.failtrade:
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                client.fail_trade(trade_id)
                print(f"open trade {trade_id} changed to failed trade")
            elif method == CliMethods.unfailtrade:
                opts = GetTradeOptionParser(method_args).parse()
                trade_id = opts.get_trade_id()
                client.unfail_trade(trade_id)
                print(f"failed trade {trade_id} changed to open trade")
            elif method == CliMethods.getpaymentacctform:
                opts = GetPaymentAccountFormOptionParser(method_args).parse()
                payment_method_id = opts.get_payment_method_id()
                json_string = client.get_payment_account_form_as_json(payment_method_id)
                json_file = CliMain._save_file_to_disk(
                    payment_method_id.lower(), ".json", json_string
                )
                print(f"payment account form {json_string}\nsaved to {json_file}\n")
                print(
                    "Edit the file, and use as the argument to a 'createpaymentacct' command."
                )
            elif method == CliMethods.createpaymentacct:
                opts = CreatePaymentAccountOptionParser(method_args).parse()
                payment_account_form = opts.get_payment_account_form()
                try:
                    with open(payment_account_form, "r") as file:
                        json_string = file.read()
                except Exception as e:
                    raise IllegalStateException(
                        f"could not read {payment_account_form}: {str(e)}"
                    )

                payment_account = client.create_payment_account(json_string)
                print("payment account saved")
                TableBuilder(
                    TableType.PAYMENT_ACCOUNT_TBL, payment_account
                ).build().print()
            elif method == CliMethods.createcryptopaymentacct:
                opts = CreateCryptoCurrencyPaymentAccountOptionParser(
                    method_args
                ).parse()
                account_name = opts.get_account_name()
                currency_code = opts.get_currency_code()
                address = opts.get_address()
                is_trade_instant = opts.get_is_trade_instant()
                payment_account = client.create_crypto_currency_payment_account(
                    account_name, currency_code, address, is_trade_instant
                )
                print("payment account saved")
                TableBuilder(
                    TableType.PAYMENT_ACCOUNT_TBL, payment_account
                ).build().print()
            elif method == CliMethods.getpaymentaccts:
                payment_accounts = client.get_payment_accounts()
                if payment_accounts:
                    TableBuilder(
                        TableType.PAYMENT_ACCOUNT_TBL, payment_accounts
                    ).build().print()
                else:
                    print("no payment accounts are saved")
            elif method == CliMethods.lockwallet:
                client.lock_wallet()
                print("wallet locked")
            elif method == CliMethods.unlockwallet:
                opts = UnlockWalletOptionParser(method_args).parse()
                wallet_password = opts.get_password()
                timeout = opts.get_unlock_timeout()
                client.unlock_wallet(wallet_password, timeout)
                print("wallet unlocked")
            elif method == CliMethods.removewalletpassword:
                opts = RemoveWalletPasswordOptionParser(method_args).parse()
                wallet_password = opts.get_password()
                client.remove_wallet_password(wallet_password)
                print("wallet decrypted")
            elif method == CliMethods.setwalletpassword:
                opts = SetWalletPasswordOptionParser(method_args).parse()
                wallet_password = opts.get_password()
                new_wallet_password = opts.get_new_password()
                client.set_wallet_password(wallet_password, new_wallet_password)
                print(
                    "wallet encrypted"
                    + (" with new password" if new_wallet_password else "")
                )
            elif method == CliMethods.registerdisputeagent:
                opts = RegisterDisputeAgentOptionParser(method_args).parse()
                dispute_agent_type = opts.get_dispute_agent_type()
                registration_key = opts.get_registration_key()
                client.register_dispute_agent(dispute_agent_type, registration_key)
                print(f"{dispute_agent_type} registered")
            elif method == CliMethods.stop:
                client.stop_server()
                print("server shutdown signal received")
            elif method == CliMethods.sendproto:
                opts = SendProtoOptionParser(method_args).parse()
                reply = client.send_proto(opts.node_address, opts.proto)
                if reply.success:
                    print("proto message sent successfully")
                else:
                    print(f"error sending proto message: {reply.error_message}")
            else:
                raise IllegalArgumentException(f"'{method_name}' is not a supported method")

    @staticmethod
    def _get_parser():
        parser = CustomArgumentParser(
            formatter_class=CustomHelpFormatter,
            allow_abbrev=False,
            add_help=False,
            usage="bisq-cli [options] <method> [params]",
        )
        parser.add_argument(
            "-h",
            "--help",
            dest=OptLabel.OPT_HELP,
            help="Print this help text.",
            action="store_true",
        )
        parser.add_argument(
            "--host",
            dest="host",
            help="rpc server hostname or ip",
            type=str,
            metavar="<String>",
            default="127.0.0.1",
        )
        parser.add_argument(
            "--port",
            dest="port",
            help="rpc server port",
            type=int,
            metavar="<Integer>",
            default=9998,
        )
        parser.add_argument(
            "--password",
            dest="password",
            help="rpc server password",
            type=str,
            metavar="<String>",
        )
        return parser

    @staticmethod
    def _print_help(parser: "CustomArgumentParser", file=sys.stdout):
        def p(*args, **kwargs):
            print(*args, file=file, **kwargs)

        try:

            p("Bisq RPC Client")
            p()
            parser.print_help(file=file)
            p()
            row_format = "{:<25}{:<52}{}"
            p(row_format.format("Method", "Params", "Description"))
            p(row_format.format("------", "------", "------------"))
            p()
            p(row_format.format(CliMethods.getversion.name, "", "Get server version"))
            p()
            p(
                row_format.format(
                    CliMethods.getnetwork.name,
                    "",
                    "Get BTC network: mainnet, testnet3, or regtest",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getdaostatus.name,
                    "",
                    "Get DAO synchronized status: true or false",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getbalance.name,
                    "[--currency-code=<bsq|btc>]",
                    "Get server wallet balances",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getaddressbalance.name,
                    "--address=<btc-address>",
                    "Get server wallet address balance",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getavgbsqprice.name,
                    "--days=<days>",
                    "Get volume weighted average bsq trade price",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getbtcprice.name,
                    "--currency-code=<currency-code>",
                    "Get current market btc price",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getfundingaddresses.name, "", "Get BTC funding addresses"
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getunusedbsqaddress.name, "", "Get unused BSQ address"
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.sendbsq.name,
                    "--address=<bsq-address> --amount=<bsq-amount>  \\",
                    "Send BSQ",
                )
            )
            p(row_format.format("", "[--tx-fee-rate=<sats/byte>]", ""))
            p()
            p(
                row_format.format(
                    CliMethods.sendbtc.name,
                    "--address=<btc-address> --amount=<btc-amount> \\",
                    "Send BTC",
                )
            )
            p(row_format.format("", "[--tx-fee-rate=<sats/byte>]", ""))
            p(row_format.format("", '[--memo=<"memo">]', ""))
            p()
            p(
                row_format.format(
                    CliMethods.verifybsqsenttoaddress.name,
                    "--address=<bsq-address> --amount=<bsq-amount>",
                    "Verify amount was sent to BSQ wallet address",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.gettxfeerate.name,
                    "",
                    "Get current tx fee rate in sats/byte",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.settxfeerate.name,
                    "--tx-fee-rate=<sats/byte>",
                    "Set custom tx fee rate in sats/byte",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.unsettxfeerate.name, "", "Unset custom tx fee rate"
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.gettransactions.name, "", "Get transactions"
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.gettransaction.name,
                    "--transaction-id=<transaction-id>",
                    "Get transaction with id",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.createoffer.name,
                    "--payment-account=<payment-account-id> \\",
                    "Create and place an offer",
                )
            )
            p(row_format.format("", "--direction=<buy|sell> \\", ""))
            p(row_format.format("", "--currency-code=<currency-code> \\", ""))
            p(row_format.format("", "--amount=<btc-amount> \\", ""))
            p(row_format.format("", "[--min-amount=<min-btc-amount>] \\", ""))
            p(
                row_format.format(
                    "", "--fixed-price=<price> | --market-price-margin=<percent> \\", ""
                )
            )
            p(row_format.format("", "--security-deposit=<percent> \\", ""))
            p(row_format.format("", "[--fee-currency=<bsq|btc>]", ""))
            p(row_format.format("", "[--trigger-price=<price>]", ""))
            p(row_format.format("", "[--swap=<true|false>]", ""))
            p()
            p(
                row_format.format(
                    CliMethods.editoffer.name,
                    "--offer-id=<offer-id> \\",
                    "Edit offer with id",
                )
            )
            p(row_format.format("", "[--fixed-price=<price>] \\", ""))
            p(row_format.format("", "[--market-price-margin=<percent>] \\", ""))
            p(row_format.format("", "[--trigger-price=<price>] \\", ""))
            p(row_format.format("", "[--enabled=<true|false>]", ""))
            p()
            p(
                row_format.format(
                    CliMethods.canceloffer.name,
                    "--offer-id=<offer-id>",
                    "Cancel offer with id",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getoffer.name,
                    "--offer-id=<offer-id>",
                    "Get current offer with id",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getmyoffer.name,
                    "--offer-id=<offer-id>",
                    "Get my current offer with id",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getoffers.name,
                    "--direction=<buy|sell> \\",
                    "Get current offers",
                )
            )
            p(row_format.format("", "--currency-code=<currency-code>", ""))
            p()
            p(
                row_format.format(
                    CliMethods.getmyoffers.name,
                    "--direction=<buy|sell> \\",
                    "Get my current offers",
                )
            )
            p(row_format.format("", "--currency-code=<currency-code>", ""))
            p()
            p(
                row_format.format(
                    CliMethods.takeoffer.name,
                    "--offer-id=<offer-id> \\",
                    "Take offer with id",
                )
            )
            p(row_format.format("", "[--payment-account=<payment-account-id>]", ""))
            p(row_format.format("", "[--fee-currency=<btc|bsq>]", ""))
            p(
                row_format.format(
                    "", "[--amount=<min-btc-amount >= amount <= btc-amount>]", ""
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.gettrade.name,
                    "--trade-id=<trade-id> \\",
                    "Get trade summary or full contract",
                )
            )
            p(row_format.format("", "[--show-contract=<true|false>]", ""))
            p()
            p(
                row_format.format(
                    CliMethods.gettrades.name,
                    "[--category=<open|closed|failed>]",
                    "Get open (default), closed, or failed trades",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.confirmpaymentstarted.name,
                    "--trade-id=<trade-id>",
                    "Confirm payment started",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.confirmpaymentreceived.name,
                    "--trade-id=<trade-id>",
                    "Confirm payment received",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.closetrade.name,
                    "--trade-id=<trade-id>",
                    "Close completed trade",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.withdrawfunds.name,
                    "--trade-id=<trade-id> --address=<btc-address> \\",
                    "Withdraw received trade funds to external wallet address",
                )
            )
            p(row_format.format("", '[--memo=<"memo">]', ""))
            p()
            p(
                row_format.format(
                    CliMethods.failtrade.name,
                    "--trade-id=<trade-id>",
                    "Change open trade to failed trade",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.unfailtrade.name,
                    "--trade-id=<trade-id>",
                    "Change failed trade to open trade",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getpaymentmethods.name,
                    "",
                    "Get list of supported payment account method ids",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.getpaymentacctform.name,
                    "--payment-method-id=<payment-method-id>",
                    "Get a new payment account form",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.createpaymentacct.name,
                    "--payment-account-form=<path>",
                    "Create a new payment account",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.createcryptopaymentacct.name,
                    "--account-name=<name> \\",
                    "Create a new cryptocurrency payment account",
                )
            )
            p(row_format.format("", "--currency-code=<bsq> \\", ""))
            p(row_format.format("", "--address=<bsq-address>", ""))
            p(row_format.format("", "--trade-instant=<true|false>", ""))
            p()
            p(
                row_format.format(
                    CliMethods.getpaymentaccts.name, "", "Get user payment accounts"
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.lockwallet.name,
                    "",
                    "Remove wallet password from memory, locking the wallet",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.unlockwallet.name,
                    "--wallet-password=<password> --timeout=<seconds>",
                    "Store wallet password in memory for timeout seconds",
                )
            )
            p()
            p(
                row_format.format(
                    CliMethods.setwalletpassword.name,
                    "--wallet-password=<password> \\",
                    "Encrypt wallet with password, or set new password on encrypted wallet",
                )
            )
            p(row_format.format("", "[--new-wallet-password=<new-password>]", ""))
            p()
            p(row_format.format(CliMethods.stop.name, "", "Shut down the server"))
            p()
            p("Method Help Usage: bisq-cli [options] <method> --help")
            p()
        except Exception as e:
            traceback.print_exc(file=sys.stderr)

    @staticmethod
    def _get_method_from_cmd(method_name: str):
        method_name = method_name.lower()
        try:
            return CliMethods[method_name]
        except:
            raise IllegalArgumentException(f"'{method_name}' is not a supported method")

    @staticmethod
    def _verify_string_is_valid_float(option_label: str, option_value: str):
        try:
            float(option_value)
        except ValueError:
            raise IllegalArgumentException(
                f"--{option_label}={option_value}, '{option_value}' is not a number (float)"
            )

    @staticmethod
    def _verify_string_is_valid_long(option_label: str, option_value: str):
        try:
            int(option_value)
        except ValueError:
            raise IllegalArgumentException(
                f"--{option_label}={option_value}, '{option_value}' is not a number (int)"
            )

    @staticmethod
    def _to_long(param: str) -> int:
        try:
            return int(param)
        except ValueError:
            raise IllegalArgumentException(f"'{param}' is not a number (int)")

    @staticmethod
    def _save_file_to_disk(prefix: str, suffix: str, text: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        relative_file_name = f"{prefix}_{timestamp}{suffix}"
        try:
            path = Path(relative_file_name)
            if not path.exists(relative_file_name):
                with open(relative_file_name, "w") as file:
                    file.write(text)
                return str(path.absolute())
            else:
                raise IllegalStateException(
                    f"could not overwrite existing file '{relative_file_name}'"
                )
        except Exception as e:
            raise IllegalStateException(
                f"could not create file '{relative_file_name}': {str(e)}"
            )
