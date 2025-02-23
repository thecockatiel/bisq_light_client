from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class GetOffersOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_DIRECTION}",
            help="offer direction (buy|sell)",
            dest=OptLabel.OPT_DIRECTION,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_CURRENCY_CODE}",
            help="currency code (bsq|xmr|eur|usd|...)",
            dest=OptLabel.OPT_CURRENCY_CODE,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_DIRECTION, None):
            raise IllegalArgumentException("no direction (buy|sell) specified")

        if not self.options.get(OptLabel.OPT_CURRENCY_CODE, None):
            raise IllegalArgumentException("no currency code specified")

        return self

    def get_direction(self) -> str:
        return self.options.get(OptLabel.OPT_DIRECTION)

    def get_currency_code(self) -> str:
        return self.options.get(OptLabel.OPT_CURRENCY_CODE)
