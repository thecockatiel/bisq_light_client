from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class TakeOfferOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_AMOUNT}",
            help="intended amount of btc to buy or sell",
            dest=OptLabel.OPT_AMOUNT,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_PAYMENT_ACCOUNT_ID}",
            help="id of payment account used for trade",
            dest=OptLabel.OPT_PAYMENT_ACCOUNT_ID,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_FEE_CURRENCY}",
            help="taker fee currency code (bsq|btc)",
            dest=OptLabel.OPT_FEE_CURRENCY,
            type=str,
            choices=["bsq", "btc"],
            default="btc",
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if OptLabel.OPT_AMOUNT in self.options:
            if not self.options.get(OptLabel.OPT_AMOUNT):
                raise IllegalArgumentException("no intended btc trade amount specified")
            try:
                CurrencyFormat.to_satoshis(self.options.get(OptLabel.OPT_AMOUNT))
            except Exception as e:
                raise IllegalArgumentException(f"invalid amount: {e}")
        else:
            self.options[OptLabel.OPT_AMOUNT] = "0"

        if not self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_ID, None):
            raise IllegalArgumentException("no payment account id specified")

        return self

    def get_amount(self) -> str:
        return self.options.get(OptLabel.OPT_AMOUNT)

    def get_payment_account_id(self) -> str:
        return self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_ID)

    def get_taker_fee_currency_code(self) -> str:
        return self.options.get(OptLabel.OPT_FEE_CURRENCY)
