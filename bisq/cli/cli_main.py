import argparse
from collections import defaultdict
import sys
import traceback
from typing import Any

from bisq.cli.cli_methods import CliMethods
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import CustomArgumentParser, CustomHelpFormatter


class CliMain:

    @staticmethod
    def main():
        try:
            CliMain.run()
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def run():
        options = defaultdict[str, Any](lambda: None)

        parser = CliMain.get_parser()
        
        opts_ns, non_option_args = parser.parse_known_args()
        cli_opts = {
            key: value
            for key, value in vars(opts_ns).items()
            if value is not None
        }  # get only present options

        options.update(cli_opts)

        # If neither the help opt nor a method name is present, print CLI level help
        # to stderr and throw an exception.
        if not options["helpRequested"] and not non_option_args:
            CliMain.print_help(parser, file=sys.stdout)
            raise IllegalArgumentException("no method specified")
        
        # If the help opt is present, but not a method name, print CLI level help
        # to stdout.
        if options["helpRequested"] and not non_option_args:
            CliMain.print_help(parser, file=sys.stdout)
            return

    @staticmethod
    def get_parser():
        parser = CustomArgumentParser(
            formatter_class=CustomHelpFormatter,
            allow_abbrev=False,
            add_help=False,
            usage="bisq-cli [options] <method> [params]"
        )
        parser.add_argument(
            "-h",
            "--help",
            dest="helpRequested",
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
    def print_help(parser: "CustomArgumentParser", file=sys.stdout):
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
            p(row_format.format(CliMethods.getnetwork.name, "", "Get BTC network: mainnet, testnet3, or regtest"))
            p()
            p(row_format.format(CliMethods.getdaostatus.name, "", "Get DAO synchronized status: true or false"))
            p()
            p(row_format.format(CliMethods.getbalance.name, "[--currency-code=<bsq|btc>]", "Get server wallet balances"))
            p()
            p(row_format.format(CliMethods.getaddressbalance.name, "--address=<btc-address>", "Get server wallet address balance"))
            p()
            p(row_format.format(CliMethods.getavgbsqprice.name, "--days=<days>", "Get volume weighted average bsq trade price"))
            p()
            p(row_format.format(CliMethods.getbtcprice.name, "--currency-code=<currency-code>", "Get current market btc price"))
            p()
            p(row_format.format(CliMethods.getfundingaddresses.name, "", "Get BTC funding addresses"))
            p()
            p(row_format.format(CliMethods.getunusedbsqaddress.name, "", "Get unused BSQ address"))
            p()
            p(row_format.format(CliMethods.sendbsq.name, "--address=<bsq-address> --amount=<bsq-amount>  \\", "Send BSQ"))
            p(row_format.format("", "[--tx-fee-rate=<sats/byte>]", ""))
            p()
            p(row_format.format(CliMethods.sendbtc.name, "--address=<btc-address> --amount=<btc-amount> \\", "Send BTC"))
            p(row_format.format("", "[--tx-fee-rate=<sats/byte>]", ""))
            p(row_format.format("", "[--memo=<\"memo\">]", ""))
            p()
            p(row_format.format(CliMethods.verifybsqsenttoaddress.name, "--address=<bsq-address> --amount=<bsq-amount>", "Verify amount was sent to BSQ wallet address"))
            p()
            p(row_format.format(CliMethods.gettxfeerate.name, "", "Get current tx fee rate in sats/byte"))
            p()
            p(row_format.format(CliMethods.settxfeerate.name, "--tx-fee-rate=<sats/byte>", "Set custom tx fee rate in sats/byte"))
            p()
            p(row_format.format(CliMethods.unsettxfeerate.name, "", "Unset custom tx fee rate"))
            p()
            p(row_format.format(CliMethods.gettransactions.name, "", "Get transactions"))
            p()
            p(row_format.format(CliMethods.gettransaction.name, "--transaction-id=<transaction-id>", "Get transaction with id"))
            p()
            p(row_format.format(CliMethods.createoffer.name, "--payment-account=<payment-account-id> \\", "Create and place an offer"))
            p(row_format.format("", "--direction=<buy|sell> \\", ""))
            p(row_format.format("", "--currency-code=<currency-code> \\", ""))
            p(row_format.format("", "--amount=<btc-amount> \\", ""))
            p(row_format.format("", "[--min-amount=<min-btc-amount>] \\", ""))
            p(row_format.format("", "--fixed-price=<price> | --market-price-margin=<percent> \\", ""))
            p(row_format.format("", "--security-deposit=<percent> \\", ""))
            p(row_format.format("", "[--fee-currency=<bsq|btc>]", ""))
            p(row_format.format("", "[--trigger-price=<price>]", ""))
            p(row_format.format("", "[--swap=<true|false>]", ""))
            p()
            p(row_format.format(CliMethods.editoffer.name, "--offer-id=<offer-id> \\", "Edit offer with id"))
            p(row_format.format("", "[--fixed-price=<price>] \\", ""))
            p(row_format.format("", "[--market-price-margin=<percent>] \\", ""))
            p(row_format.format("", "[--trigger-price=<price>] \\", ""))
            p(row_format.format("", "[--enabled=<true|false>]", ""))
            p()
            p(row_format.format(CliMethods.canceloffer.name, "--offer-id=<offer-id>", "Cancel offer with id"))
            p()
            p(row_format.format(CliMethods.getoffer.name, "--offer-id=<offer-id>", "Get current offer with id"))
            p()
            p(row_format.format(CliMethods.getmyoffer.name, "--offer-id=<offer-id>", "Get my current offer with id"))
            p()
            p(row_format.format(CliMethods.getoffers.name, "--direction=<buy|sell> \\", "Get current offers"))
            p(row_format.format("", "--currency-code=<currency-code>", ""))
            p()
            p(row_format.format(CliMethods.getmyoffers.name, "--direction=<buy|sell> \\", "Get my current offers"))
            p(row_format.format("", "--currency-code=<currency-code>", ""))
            p()
            p(row_format.format(CliMethods.takeoffer.name, "--offer-id=<offer-id> \\", "Take offer with id"))
            p(row_format.format("", "[--payment-account=<payment-account-id>]", ""))
            p(row_format.format("", "[--fee-currency=<btc|bsq>]", ""))
            p(row_format.format("", "[--amount=<min-btc-amount >= amount <= btc-amount>]", ""))
            p()
            p(row_format.format(CliMethods.gettrade.name, "--trade-id=<trade-id> \\", "Get trade summary or full contract"))
            p(row_format.format("", "[--show-contract=<true|false>]", ""))
            p()
            p(row_format.format(CliMethods.gettrades.name, "[--category=<open|closed|failed>]", "Get open (default), closed, or failed trades"))
            p()
            p(row_format.format(CliMethods.confirmpaymentstarted.name, "--trade-id=<trade-id>", "Confirm payment started"))
            p()
            p(row_format.format(CliMethods.confirmpaymentreceived.name, "--trade-id=<trade-id>", "Confirm payment received"))
            p()
            p(row_format.format(CliMethods.closetrade.name, "--trade-id=<trade-id>", "Close completed trade"))
            p()
            p(row_format.format(CliMethods.withdrawfunds.name, "--trade-id=<trade-id> --address=<btc-address> \\", "Withdraw received trade funds to external wallet address"))
            p(row_format.format("", "[--memo=<\"memo\">]", ""))
            p()
            p(row_format.format(CliMethods.failtrade.name, "--trade-id=<trade-id>", "Change open trade to failed trade"))
            p()
            p(row_format.format(CliMethods.unfailtrade.name, "--trade-id=<trade-id>", "Change failed trade to open trade"))
            p()
            p(row_format.format(CliMethods.getpaymentmethods.name, "", "Get list of supported payment account method ids"))
            p()
            p(row_format.format(CliMethods.getpaymentacctform.name, "--payment-method-id=<payment-method-id>", "Get a new payment account form"))
            p()
            p(row_format.format(CliMethods.createpaymentacct.name, "--payment-account-form=<path>", "Create a new payment account"))
            p()
            p(row_format.format(CliMethods.createcryptopaymentacct.name, "--account-name=<name> \\", "Create a new cryptocurrency payment account"))
            p(row_format.format("", "--currency-code=<bsq> \\", ""))
            p(row_format.format("", "--address=<bsq-address>", ""))
            p(row_format.format("", "--trade-instant=<true|false>", ""))
            p()
            p(row_format.format(CliMethods.getpaymentaccts.name, "", "Get user payment accounts"))
            p()
            p(row_format.format(CliMethods.lockwallet.name, "", "Remove wallet password from memory, locking the wallet"))
            p()
            p(row_format.format(CliMethods.unlockwallet.name, "--wallet-password=<password> --timeout=<seconds>", "Store wallet password in memory for timeout seconds"))
            p()
            p(row_format.format(CliMethods.setwalletpassword.name, "--wallet-password=<password> \\", "Encrypt wallet with password, or set new password on encrypted wallet"))
            p(row_format.format("", "[--new-wallet-password=<new-password>]", ""))
            p()
            p(row_format.format(CliMethods.stop.name, "", "Shut down the server"))
            p()
            p("Method Help Usage: bisq-cli [options] <method> --help")
            p()
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            