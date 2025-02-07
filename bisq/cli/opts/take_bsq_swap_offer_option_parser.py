from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class TakeBsqSwapOfferOptionParser(SimpleMethodOptionParser):

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
            help="not used when taking bsq swaps",
            dest=OptLabel.OPT_PAYMENT_ACCOUNT_ID,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_FEE_CURRENCY}",
            help="not used when taking bsq swaps",
            dest=OptLabel.OPT_FEE_CURRENCY,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_ID, None):
            raise IllegalArgumentException(
                f"the {OptLabel.OPT_PAYMENT_ACCOUNT_ID} param is not used for swaps; the internal default swap account is always used"
            )

        if self.options.get(OptLabel.OPT_FEE_CURRENCY, None):
            raise IllegalArgumentException(
                f"the {OptLabel.OPT_FEE_CURRENCY} param is not used for swaps; fees are always paid in bsq"
            )

        if OptLabel.OPT_AMOUNT in self.options:
            if not self.options.get(OptLabel.OPT_AMOUNT):
                raise IllegalArgumentException("no intended btc trade amount specified")
            try:
                CurrencyFormat.to_satoshis(self.options.get(OptLabel.OPT_AMOUNT))
            except Exception as e:
                raise IllegalArgumentException(f"invalid amount: {e}")
        else:
            self.options[OptLabel.OPT_AMOUNT] = "0"

        return self

    def get_amount(self) -> str:
        return self.options.get(OptLabel.OPT_AMOUNT)
