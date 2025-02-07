from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class CreateCryptoCurrencyPaymentAccountOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_ACCOUNT_NAME}",
            help="crypto currency account name",
            dest=OptLabel.OPT_ACCOUNT_NAME,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_CURRENCY_CODE}",
            help="crypto currency code (bsq|xmr)",
            dest=OptLabel.OPT_CURRENCY_CODE,
            type=str,
            choices=["bsq", "xmr"],
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_ADDRESS}",
            help="altcoin address",
            dest=OptLabel.OPT_ADDRESS,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_TRADE_INSTANT}",
            help="create trade instant account",
            dest=OptLabel.OPT_TRADE_INSTANT,
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_ACCOUNT_NAME, None):
            raise IllegalArgumentException("no payment account name specified")

        # currency code is checked and enforced by parser

        if not self.options.get(OptLabel.OPT_ADDRESS, None):
            raise IllegalArgumentException(
                "no {} address specified".format(
                    self.options.get(OptLabel.OPT_CURRENCY_CODE)
                )
            )

        return self

    def get_account_name(self):
        return self.options.get(OptLabel.OPT_ACCOUNT_NAME)

    def get_currency_code(self):
        return self.options.get(OptLabel.OPT_CURRENCY_CODE)

    def get_address(self):
        return self.options.get(OptLabel.OPT_ADDRESS)

    def get_is_trade_instant(self):
        return self.options.get(OptLabel.OPT_TRADE_INSTANT, False)
